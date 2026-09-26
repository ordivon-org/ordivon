using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;
using System.Runtime.InteropServices;

internal static class OrdivonWindowsPrivilegedBroker
{
    private const int SchemaVersion = 1;
    private const int MaxMessageBytes = 262144;
    private const int MaxCaptureBytes = 65536;
    private const int ClientConnectTimeoutMs = 5000;
    private const int CaptureTimeoutMs = 10000;
    [StructLayout(LayoutKind.Sequential)]
    private struct FileTime
    {
        public uint Low;
        public uint High;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetProcessTimes(
        IntPtr process,
        out FileTime creation,
        out FileTime exit,
        out FileTime kernel,
        out FileTime user);

    private sealed class Options
    {
        public bool Client;
        public bool Service;
        public bool ConsoleServer;
        public string ServiceName;
        public string PipeName;
        public string LauncherPath;
        public string LauncherSha256;
        public string AllowedClientSid;
        public string AllowedBundleRoot;
        public string MaterializationConfig;
    }

    private sealed class BrokerService : ServiceBase
    {
        private readonly Options options;
        private Thread worker;

        public BrokerService(Options value)
        {
            options = value;
            ServiceName = value.ServiceName;
            CanStop = true;
            CanShutdown = true;
            AutoLog = true;
        }

        protected override void OnStart(string[] args)
        {
            worker = new Thread(delegate()
            {
                try
                {
                    RunServer(options);
                }
                catch (Exception error)
                {
                    try { EventLog.WriteEntry(ServiceName, "Privileged broker failed: " + error, EventLogEntryType.Error); }
                    catch { }
                    Environment.ExitCode = 1;
                }
            });
            worker.IsBackground = true;
            worker.Start();
        }

        protected override void OnStop()
        {
            RequestStop();
            if (worker != null && !worker.Join(5000))
            {
                try { EventLog.WriteEntry(ServiceName, "Privileged broker did not stop within 5 seconds.", EventLogEntryType.Warning); }
                catch { }
            }
        }

        protected override void OnShutdown()
        {
            OnStop();
            base.OnShutdown();
        }
    }

    private static readonly object PipeLock = new object();
    private static NamedPipeServerStream CurrentPipe;
    private static volatile bool StopRequested;

    public static int Main(string[] args)
    {
        try
        {
            Options options = ParseOptions(args);
            if (options.Client)
            {
                return RunClient(options);
            }
            ValidateServerConfiguration(options);
            if (options.Service)
            {
                EnsureLocalSystem();
                ServiceBase.Run(new BrokerService(options));
                return 0;
            }
            if (options.ConsoleServer)
            {
                RunServer(options);
                return 0;
            }
            throw new InvalidOperationException("one of --client, --service, or --console-server is required");
        }
        catch (Exception error)
        {
            Console.Error.WriteLine("ordivon-windows-privileged-broker: " + error.Message);
            return 125;
        }
    }

    private static Options ParseOptions(string[] args)
    {
        Options options = new Options();
        for (int i = 0; i < args.Length; ++i)
        {
            string current = args[i];
            if (current == "--client") { options.Client = true; continue; }
            if (current == "--service") { options.Service = true; continue; }
            if (current == "--console-server") { options.ConsoleServer = true; continue; }
            if (i + 1 >= args.Length) throw new InvalidOperationException("missing value for " + current);
            string value = args[++i];
            if (current == "--service-name") options.ServiceName = value;
            else if (current == "--pipe-name") options.PipeName = value;
            else if (current == "--launcher-path") options.LauncherPath = value;
            else if (current == "--launcher-sha256") options.LauncherSha256 = value;
            else if (current == "--allowed-client-sid") options.AllowedClientSid = value;
            else if (current == "--allowed-bundle-root") options.AllowedBundleRoot = value;
            else if (current == "--materialization-config") options.MaterializationConfig = value;
            else throw new InvalidOperationException("unknown option: " + current);
        }

        int modes = (options.Client ? 1 : 0) + (options.Service ? 1 : 0) + (options.ConsoleServer ? 1 : 0);
        if (modes != 1) throw new InvalidOperationException("exactly one broker mode is required");
        if (String.IsNullOrWhiteSpace(options.PipeName) || !IsSafeName(options.PipeName, 128))
            throw new InvalidOperationException("--pipe-name is invalid");
        if (options.Client) return options;
        if (String.IsNullOrWhiteSpace(options.ServiceName) || !IsSafeName(options.ServiceName, 128))
            throw new InvalidOperationException("--service-name is invalid");
        if (String.IsNullOrWhiteSpace(options.LauncherPath))
            throw new InvalidOperationException("--launcher-path is required");
        if (String.IsNullOrWhiteSpace(options.LauncherSha256) || !IsLowerSha256(options.LauncherSha256))
            throw new InvalidOperationException("--launcher-sha256 must be lowercase SHA-256 hex");
        if (String.IsNullOrWhiteSpace(options.AllowedClientSid))
            throw new InvalidOperationException("--allowed-client-sid is required");
        if (String.IsNullOrWhiteSpace(options.AllowedBundleRoot))
            throw new InvalidOperationException("--allowed-bundle-root is required");
        return options;
    }

    private static bool IsSafeName(string value, int max)
    {
        if (value.Length == 0 || value.Length > max) return false;
        for (int i = 0; i < value.Length; ++i)
        {
            char c = value[i];
            if (!(Char.IsLetterOrDigit(c) || c == '.' || c == '_' || c == '-')) return false;
        }
        return true;
    }

    private static bool IsLowerSha256(string value)
    {
        if (value.Length != 64) return false;
        for (int i = 0; i < value.Length; ++i)
        {
            char c = value[i];
            if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
        }
        return true;
    }

    private static void ValidateServerConfiguration(Options options)
    {
        options.LauncherPath = Path.GetFullPath(NormalizeBrokerPath(options.LauncherPath));
        if (!File.Exists(options.LauncherPath)) throw new InvalidOperationException("launcher does not exist");
        if (!String.Equals(Sha256File(options.LauncherPath), options.LauncherSha256, StringComparison.Ordinal))
            throw new InvalidOperationException("launcher SHA-256 does not match configured digest");
        options.AllowedBundleRoot = Path.GetFullPath(NormalizeBrokerPath(options.AllowedBundleRoot));
        if (!Directory.Exists(options.AllowedBundleRoot)) throw new InvalidOperationException("allowed bundle root does not exist");
        if (!String.IsNullOrWhiteSpace(options.MaterializationConfig))
        {
            options.MaterializationConfig = Path.GetFullPath(NormalizeBrokerPath(options.MaterializationConfig));
            if (!File.Exists(options.MaterializationConfig))
                throw new InvalidOperationException("materialization config does not exist");
        }
        new SecurityIdentifier(options.AllowedClientSid);
    }

    private static void EnsureLocalSystem()
    {
        WindowsIdentity identity = WindowsIdentity.GetCurrent(TokenAccessLevels.Query);
        if (identity.User == null || !identity.User.IsWellKnown(WellKnownSidType.LocalSystemSid))
            throw new InvalidOperationException("privileged broker service must run as LocalSystem");
    }

    private static PipeSecurity BuildPipeSecurity(string allowedClientSid)
    {
        PipeSecurity security = new PipeSecurity();
        security.SetAccessRuleProtection(true, false);
        security.AddAccessRule(new PipeAccessRule(
            new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null),
            PipeAccessRights.FullControl, AccessControlType.Allow));
        security.AddAccessRule(new PipeAccessRule(
            new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null),
            PipeAccessRights.FullControl, AccessControlType.Allow));
        security.AddAccessRule(new PipeAccessRule(
            new SecurityIdentifier(allowedClientSid),
            PipeAccessRights.ReadWrite, AccessControlType.Allow));
        return security;
    }

    private static void RunServer(Options options)
    {
        StopRequested = false;
        while (!StopRequested)
        {
            NamedPipeServerStream pipe = null;
            try
            {
                pipe = new NamedPipeServerStream(
                    options.PipeName,
                    PipeDirection.InOut,
                    1,
                    PipeTransmissionMode.Byte,
                    PipeOptions.WriteThrough,
                    MaxMessageBytes,
                    MaxMessageBytes,
                    BuildPipeSecurity(options.AllowedClientSid));
                lock (PipeLock) { CurrentPipe = pipe; }
                pipe.WaitForConnection();
                if (StopRequested) break;
                string requestJson = ReadFrame(pipe);
                string responseJson;
                try
                {
                    responseJson = HandleRequest(options, requestJson);
                }
                catch (Exception error)
                {
                    responseJson = SerializeError(ExtractRequestId(requestJson), "BROKER_REQUEST_REJECTED", error.Message);
                }
                WriteFrame(pipe, responseJson);
            }
            catch (ObjectDisposedException)
            {
                if (!StopRequested) throw;
            }
            catch (IOException)
            {
                if (!StopRequested) throw;
            }
            finally
            {
                lock (PipeLock)
                {
                    if (Object.ReferenceEquals(CurrentPipe, pipe)) CurrentPipe = null;
                }
                if (pipe != null) pipe.Dispose();
            }
        }
    }

    private static void RequestStop()
    {
        StopRequested = true;
        lock (PipeLock)
        {
            if (CurrentPipe != null)
            {
                try { CurrentPipe.Dispose(); }
                catch { }
            }
        }
    }

    private static int RunClient(Options options)
    {
        string request = Console.In.ReadToEnd();
        if (Encoding.UTF8.GetByteCount(request) > MaxMessageBytes)
            throw new InvalidOperationException("client request exceeds broker message limit");
        using (NamedPipeClientStream pipe = new NamedPipeClientStream(
            ".", options.PipeName, PipeDirection.InOut, PipeOptions.WriteThrough,
            TokenImpersonationLevel.Identification))
        {
            pipe.Connect(ClientConnectTimeoutMs);
            WriteFrame(pipe, request);
            string response = ReadFrame(pipe);
            byte[] responseBytes = Encoding.UTF8.GetBytes(response);
            using (Stream stdout = Console.OpenStandardOutput())
            {
                stdout.Write(responseBytes, 0, responseBytes.Length);
                stdout.Flush();
            }
        }
        return 0;
    }

    private static string HandleRequest(Options options, string json)
    {
        JavaScriptSerializer serializer = new JavaScriptSerializer();
        serializer.MaxJsonLength = MaxMessageBytes;
        object raw = serializer.DeserializeObject(json);
        IDictionary<string, object> request = raw as IDictionary<string, object>;
        if (request == null) throw new InvalidOperationException("request must be a JSON object");
        int schemaVersion = GetInt(request, "schemaVersion");
        if (schemaVersion != SchemaVersion) throw new InvalidOperationException("unsupported schemaVersion");
        string requestId = GetString(request, "requestId");
        if (!IsSafeRequestId(requestId)) throw new InvalidOperationException("requestId is invalid");
        string operation = GetString(request, "operation");

        VerifyPinnedLauncher(options);

        if (operation == "capture")
        {
            List<string> launcherArgs = GetStringList(request, "launcherArgs");
            ValidateCaptureArgs(launcherArgs);
            ProcessResult capture = CaptureLauncher(options.LauncherPath, launcherArgs);
            Dictionary<string, object> result = BaseSuccess(requestId, "capture");
            result["exitCode"] = capture.ExitCode;
            result["stdout"] = capture.Stdout;
            result["stderr"] = capture.Stderr;
            return serializer.Serialize(result);
        }
        if (operation == "spawn")
        {
            List<string> launcherArgs = GetStringList(request, "launcherArgs");
            string launcherStderrPath = GetString(request, "launcherStderrPath");
            launcherStderrPath = ValidateSpawnArgs(options, launcherArgs, launcherStderrPath);
            Process child = StartLauncher(options.LauncherPath, launcherArgs, false, true);
            ulong creation = ProcessCreationTimeFileTime(child);
            int processId = child.Id;
            BeginLauncherStderrPump(child, launcherStderrPath);
            Dictionary<string, object> result = BaseSuccess(requestId, "spawn");
            result["processId"] = processId;
            result["processCreationTimeFileTime"] = creation;
            return serializer.Serialize(result);
        }
        if (operation == "materialize")
        {
            string binding = GetString(request, "binding");
            if (!IsSafeName(binding, 128)) throw new InvalidOperationException("binding is invalid");
            MaterializationResult materialized = MaterializeConfiguredBinding(options, binding);
            Dictionary<string, object> result = BaseSuccess(requestId, "materialize");
            result["binding"] = binding;
            result["disposition"] = materialized.Disposition;
            result["endpointCount"] = materialized.EndpointCount;
            result["bytes"] = materialized.Bytes;
            result["secretValuesReturned"] = false;
            result["secretDigestsReturned"] = false;
            return serializer.Serialize(result);
        }
        throw new InvalidOperationException("unsupported broker operation");
    }

    private static void VerifyPinnedLauncher(Options options)
    {
        if (!File.Exists(options.LauncherPath))
            throw new InvalidOperationException("pinned launcher is unavailable");
        string observed = Sha256File(options.LauncherPath);
        if (!String.Equals(observed, options.LauncherSha256, StringComparison.Ordinal))
            throw new InvalidOperationException("pinned launcher digest changed");
    }

    private static MaterializationBinding LoadMaterializationBinding(Options options, string binding)
    {
        if (String.IsNullOrWhiteSpace(options.MaterializationConfig))
            throw new InvalidOperationException("credential materialization is not configured");
        FileInfo configInfo = new FileInfo(options.MaterializationConfig);
        if (!configInfo.Exists || (configInfo.Attributes & FileAttributes.ReparsePoint) != 0)
            throw new InvalidOperationException("materialization config must be a regular non-reparse file");
        if (configInfo.Length <= 0 || configInfo.Length > 65536)
            throw new InvalidOperationException("materialization config size is invalid");
        ValidateOperatorOnlyFileAcl(options.MaterializationConfig, "materialization config");

        JavaScriptSerializer serializer = new JavaScriptSerializer();
        serializer.MaxJsonLength = 65536;
        IDictionary<string, object> root = serializer.DeserializeObject(
            File.ReadAllText(options.MaterializationConfig, Encoding.UTF8)) as IDictionary<string, object>;
        if (root == null || GetInt(root, "schemaVersion") != 1)
            throw new InvalidOperationException("materialization config must be schemaVersion 1");
        object bindingsRaw;
        if (!root.TryGetValue("bindings", out bindingsRaw))
            throw new InvalidOperationException("materialization config requires bindings");
        IDictionary<string, object> bindings = bindingsRaw as IDictionary<string, object>;
        if (bindings == null) throw new InvalidOperationException("materialization config bindings must be an object");
        object rowRaw;
        if (!bindings.TryGetValue(binding, out rowRaw))
            throw new InvalidOperationException("materialization binding is not configured");
        IDictionary<string, object> row = rowRaw as IDictionary<string, object>;
        if (row == null) throw new InvalidOperationException("materialization binding must be an object");
        if (!String.Equals(GetString(row, "kind"), "shared-bearer", StringComparison.Ordinal))
            throw new InvalidOperationException("materialization binding kind is unsupported");
        string authorityPath = Path.GetFullPath(NormalizeBrokerPath(GetString(row, "authorityPath")));
        int tokenBytes = GetInt(row, "tokenBytes");
        if (tokenBytes < 32 || tokenBytes > 96)
            throw new InvalidOperationException("materialization tokenBytes must be between 32 and 96");
        object endpointsRaw;
        if (!row.TryGetValue("endpoints", out endpointsRaw))
            throw new InvalidOperationException("materialization binding requires endpoints");
        IEnumerable endpointValues = endpointsRaw as IEnumerable;
        if (endpointValues == null || endpointsRaw is string)
            throw new InvalidOperationException("materialization endpoints must be an array");
        List<MaterializationEndpoint> endpoints = new List<MaterializationEndpoint>();
        HashSet<string> paths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (object endpointRaw in endpointValues)
        {
            IDictionary<string, object> endpoint = endpointRaw as IDictionary<string, object>;
            if (endpoint == null) throw new InvalidOperationException("materialization endpoint must be an object");
            string path = Path.GetFullPath(NormalizeBrokerPath(GetString(endpoint, "path")));
            string serviceName = GetString(endpoint, "serviceName");
            if (!IsSafeName(serviceName, 128)) throw new InvalidOperationException("materialization endpoint serviceName is invalid");
            if (!paths.Add(path)) throw new InvalidOperationException("materialization endpoint paths must be unique");
            endpoints.Add(new MaterializationEndpoint { Path = path, ServiceName = serviceName });
        }
        if (endpoints.Count < 2 || endpoints.Count > 8)
            throw new InvalidOperationException("materialization binding must have between 2 and 8 endpoints");
        return new MaterializationBinding {
            AuthorityPath = authorityPath,
            TokenBytes = tokenBytes,
            Endpoints = endpoints,
        };
    }

    private static void ValidateOperatorOnlyFileAcl(string path, string label)
    {
        FileSecurity security = new FileInfo(path).GetAccessControl(AccessControlSections.Access);
        if (!security.AreAccessRulesProtected)
            throw new InvalidOperationException(label + " DACL must be protected");
        SecurityIdentifier system = new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null);
        SecurityIdentifier administrators = new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null);
        AuthorizationRuleCollection rules = security.GetAccessRules(true, false, typeof(SecurityIdentifier));
        if (rules.Count == 0) throw new InvalidOperationException(label + " has no explicit DACL entries");
        bool sawSystem = false;
        bool sawAdministrators = false;
        foreach (FileSystemAccessRule rule in rules)
        {
            SecurityIdentifier sid = rule.IdentityReference as SecurityIdentifier;
            if (sid == null || rule.AccessControlType != AccessControlType.Allow)
                throw new InvalidOperationException(label + " contains a non-allow or non-SID DACL entry");
            bool isSystem = sid.Equals(system);
            bool isAdministrators = sid.Equals(administrators);
            if (!isSystem && !isAdministrators)
                throw new InvalidOperationException(label + " grants access to an unexpected principal");
            if ((rule.FileSystemRights & FileSystemRights.FullControl) != FileSystemRights.FullControl)
                throw new InvalidOperationException(label + " operator principals require FullControl");
            sawSystem |= isSystem;
            sawAdministrators |= isAdministrators;
        }
        if (!sawSystem || !sawAdministrators)
            throw new InvalidOperationException(label + " omits SYSTEM or Builtin Administrators");
    }

    private static FileSecurity BuildPrivateFileSecurity(string serviceName)
    {
        SecurityIdentifier system = new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null);
        SecurityIdentifier administrators = new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid, null);
        FileSecurity security = new FileSecurity();
        security.SetAccessRuleProtection(true, false);
        security.SetOwner(administrators);
        security.AddAccessRule(new FileSystemAccessRule(system, FileSystemRights.FullControl, AccessControlType.Allow));
        security.AddAccessRule(new FileSystemAccessRule(administrators, FileSystemRights.FullControl, AccessControlType.Allow));
        if (!String.IsNullOrWhiteSpace(serviceName))
        {
            SecurityIdentifier serviceSid = (SecurityIdentifier)new NTAccount("NT SERVICE\\" + serviceName)
                .Translate(typeof(SecurityIdentifier));
            security.AddAccessRule(new FileSystemAccessRule(serviceSid, FileSystemRights.Read, AccessControlType.Allow));
        }
        return security;
    }

    private static byte[] ReadBearerFile(string path, string label)
    {
        FileInfo info = new FileInfo(path);
        if (!info.Exists || (info.Attributes & FileAttributes.ReparsePoint) != 0)
            throw new InvalidOperationException(label + " must be a regular non-reparse file");
        if (info.Length <= 0 || info.Length > 16384)
            throw new InvalidOperationException(label + " size is invalid");
        byte[] value = File.ReadAllBytes(path);
        string text = Encoding.UTF8.GetString(value);
        if (String.IsNullOrEmpty(text))
            throw new InvalidOperationException(label + " is empty");
        for (int i = 0; i < text.Length; ++i)
            if (Char.IsWhiteSpace(text[i]))
                throw new InvalidOperationException(label + " must contain one non-whitespace bearer value");
        return value;
    }

    private static bool EqualBytes(byte[] left, byte[] right)
    {
        if (left == null || right == null || left.Length != right.Length) return false;
        int difference = 0;
        for (int i = 0; i < left.Length; ++i) difference |= left[i] ^ right[i];
        return difference == 0;
    }

    private static void WritePrivateFileAtomic(string path, byte[] value, string serviceName)
    {
        string parent = Path.GetDirectoryName(path);
        if (String.IsNullOrWhiteSpace(parent) || !Directory.Exists(parent))
            throw new InvalidOperationException("materialization destination parent does not exist");
        DirectoryInfo parentInfo = new DirectoryInfo(parent);
        if ((parentInfo.Attributes & FileAttributes.ReparsePoint) != 0)
            throw new InvalidOperationException("materialization destination parent must not be a reparse point");
        string temporary = Path.Combine(parent, ".ordivon-materialize-" + Guid.NewGuid().ToString("N") + ".tmp");
        try
        {
            using (FileStream stream = new FileStream(
                temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough))
            {
                stream.Write(value, 0, value.Length);
                stream.Flush(true);
            }
            new FileInfo(temporary).SetAccessControl(BuildPrivateFileSecurity(serviceName));
            File.Move(temporary, path);
        }
        finally
        {
            try { if (File.Exists(temporary)) File.Delete(temporary); }
            catch { }
        }
    }

    private static byte[] EnsureAuthorityBearer(MaterializationBinding binding, out bool created)
    {
        created = false;
        if (File.Exists(binding.AuthorityPath))
        {
            ValidateOperatorOnlyFileAcl(binding.AuthorityPath, "materialization authority file");
            return ReadBearerFile(binding.AuthorityPath, "materialization authority file");
        }
        byte[] random = new byte[binding.TokenBytes];
        using (RandomNumberGenerator generator = RandomNumberGenerator.Create())
            generator.GetBytes(random);
        byte[] bearer = Encoding.UTF8.GetBytes(Convert.ToBase64String(random));
        Array.Clear(random, 0, random.Length);
        try
        {
            WritePrivateFileAtomic(binding.AuthorityPath, bearer, null);
            ValidateOperatorOnlyFileAcl(binding.AuthorityPath, "materialization authority file");
            created = true;
            return bearer;
        }
        catch
        {
            Array.Clear(bearer, 0, bearer.Length);
            throw;
        }
    }

    private static MaterializationResult MaterializeConfiguredBinding(Options options, string bindingName)
    {
        MaterializationBinding binding = LoadMaterializationBinding(options, bindingName);
        bool authorityCreated;
        byte[] authority = EnsureAuthorityBearer(binding, out authorityCreated);
        int createdEndpoints = 0;
        try
        {
            foreach (MaterializationEndpoint endpoint in binding.Endpoints)
            {
                using (ServiceController service = new ServiceController(endpoint.ServiceName))
                {
                    string observed = service.ServiceName;
                    if (!String.Equals(observed, endpoint.ServiceName, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidOperationException("materialization endpoint service identity mismatch");
                }
                if (File.Exists(endpoint.Path))
                {
                    byte[] existing = ReadBearerFile(endpoint.Path, "materialized endpoint");
                    try
                    {
                        if (!EqualBytes(authority, existing))
                            throw new InvalidOperationException("materialized endpoint conflicts with authority bearer");
                    }
                    finally
                    {
                        Array.Clear(existing, 0, existing.Length);
                    }
                    continue;
                }
                WritePrivateFileAtomic(endpoint.Path, authority, endpoint.ServiceName);
                ++createdEndpoints;
            }
            return new MaterializationResult {
                Disposition = authorityCreated || createdEndpoints > 0 ? "materialized" : "existing",
                EndpointCount = binding.Endpoints.Count,
                Bytes = authority.Length,
            };
        }
        finally
        {
            Array.Clear(authority, 0, authority.Length);
        }
    }

    private sealed class MaterializationEndpoint
    {
        public string Path;
        public string ServiceName;
    }

    private sealed class MaterializationBinding
    {
        public string AuthorityPath;
        public int TokenBytes;
        public List<MaterializationEndpoint> Endpoints;
    }

    private sealed class MaterializationResult
    {
        public string Disposition;
        public int EndpointCount;
        public int Bytes;
    }

    private sealed class ProcessResult
    {
        public int ExitCode;
        public string Stdout;
        public string Stderr;
    }

    private static ProcessResult CaptureLauncher(string launcherPath, IList<string> args)
    {
        using (Process process = StartLauncher(launcherPath, args, true, true))
        {
            string stdout = process.StandardOutput.ReadToEnd();
            string stderr = process.StandardError.ReadToEnd();
            if (!process.WaitForExit(CaptureTimeoutMs))
            {
                try { process.Kill(); }
                catch { }
                throw new InvalidOperationException("launcher capture operation timed out");
            }
            if (Encoding.UTF8.GetByteCount(stdout) > MaxCaptureBytes || Encoding.UTF8.GetByteCount(stderr) > MaxCaptureBytes)
                throw new InvalidOperationException("launcher capture output exceeded bounded size");
            return new ProcessResult { ExitCode = process.ExitCode, Stdout = stdout, Stderr = stderr };
        }
    }

    private static Process StartLauncher(
        string launcherPath,
        IList<string> args,
        bool redirectStdout,
        bool redirectStderr)
    {
        ProcessStartInfo info = new ProcessStartInfo();
        info.FileName = launcherPath;
        info.Arguments = JoinArguments(args);
        info.WorkingDirectory = Path.GetDirectoryName(launcherPath);
        info.UseShellExecute = false;
        info.CreateNoWindow = true;
        info.RedirectStandardOutput = redirectStdout;
        info.RedirectStandardError = redirectStderr;
        Process process = new Process();
        process.StartInfo = info;
        if (!process.Start()) throw new InvalidOperationException("failed to start pinned launcher");
        return process;
    }

    private static void BeginLauncherStderrPump(Process process, string stderrPath)
    {
        FileStream carrier = null;
        try
        {
            carrier = new FileStream(
                stderrPath,
                FileMode.Create,
                FileAccess.Write,
                FileShare.Read,
                4096,
                FileOptions.WriteThrough);
        }
        catch
        {
            try { process.Kill(); }
            catch { }
            process.Dispose();
            throw;
        }

        Thread pump = new Thread(delegate()
        {
            try
            {
                using (carrier)
                {
                    process.StandardError.BaseStream.CopyTo(carrier);
                    carrier.Flush(true);
                }
            }
            catch
            {
                try { process.Kill(); }
                catch { }
            }
            finally
            {
                process.Dispose();
            }
        });
        pump.IsBackground = true;
        pump.Start();
    }

    private static void ValidateCaptureArgs(IList<string> args)
    {
        if (args.Count == 0) throw new InvalidOperationException("capture launcherArgs are empty");
        bool runtimeContext = args[0] == "--describe-runtime-context";
        bool owner = args[0] == "--describe-process-owner";
        bool deadline = args[0] == "--terminate-process-owner-for-deadline";
        if (!(runtimeContext || owner || deadline))
            throw new InvalidOperationException("capture operation is not an approved launcher probe");
        if (runtimeContext && !ContainsPair(args, "--authority", "elevated"))
            throw new InvalidOperationException("runtime context broker probe must request elevated authority");
        if (!runtimeContext && Contains(args, "--authority"))
            throw new InvalidOperationException("owner probes must not carry authority arguments");
        if (Contains(args, "--payload-privilege"))
        {
            if (!runtimeContext
                || !ContainsPair(args, "--identity", "active_user")
                || !ContainsPair(args, "--payload-privilege", "elevated"))
            {
                throw new InvalidOperationException(
                    "broker capture payload privilege is restricted to active_user elevated runtime-context probes");
            }
        }
        if (Contains(args, "--executable") || Contains(args, "--runtime-bundle"))
            throw new InvalidOperationException("capture operation cannot request process execution");
    }

    private static string ValidateSpawnArgs(
        Options options,
        IList<string> args,
        string launcherStderrPath)
    {
        if (!ContainsPair(args, "--authority", "elevated"))
            throw new InvalidOperationException("broker spawn requires elevated authority");
        if (Contains(args, "--payload-privilege")
            && (!ContainsPair(args, "--identity", "active_user")
                || !ContainsPair(args, "--payload-privilege", "elevated")))
        {
            throw new InvalidOperationException(
                "broker spawn payload privilege is restricted to active_user elevated Runtime execution");
        }
        string bundle = ValueAfter(args, "--runtime-bundle");
        if (bundle == null) throw new InvalidOperationException("broker spawn requires --runtime-bundle");
        if (!Contains(args, "--runtime-job-id") || !Contains(args, "--runtime-attempt-id")
            || !Contains(args, "--runtime-launch-token-digest") || !Contains(args, "--runtime-request-digest")
            || !Contains(args, "--job-name") || !Contains(args, "--executable"))
            throw new InvalidOperationException("broker spawn omitted required Runtime launcher identity");
        if (Contains(args, "--emit-launcher-start"))
            throw new InvalidOperationException("broker spawn requires parent-owned launcher-start evidence");
        string fullBundle = Path.GetFullPath(NormalizeBrokerPath(bundle));
        if (!IsUnderRoot(fullBundle, options.AllowedBundleRoot))
            throw new InvalidOperationException("runtime bundle is outside broker authority root");
        if (!Directory.Exists(fullBundle))
            throw new InvalidOperationException("runtime bundle does not exist");
        string fullStderr = Path.GetFullPath(NormalizeBrokerPath(launcherStderrPath));
        string expectedStderr = Path.GetFullPath(Path.Combine(fullBundle, "launcher-stderr.log"));
        if (!String.Equals(fullStderr, expectedStderr, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException(
                "launcher stderr carrier must be the canonical Runtime bundle launcher-stderr.log");
        return fullStderr;
    }

    private static bool IsUnderRoot(string path, string root)
    {
        string normalizedRoot = Path.GetFullPath(NormalizeBrokerPath(root))
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        string normalizedPath = Path.GetFullPath(NormalizeBrokerPath(path));
        return normalizedPath.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase);
    }

    private static string NormalizeBrokerPath(string value)
    {
        if (String.IsNullOrWhiteSpace(value))
        {
            return value;
        }
        if (value.StartsWith(@"\\?\UNC\", StringComparison.OrdinalIgnoreCase))
        {
            return @"\\" + value.Substring(8);
        }
        if (value.StartsWith(@"\\?\", StringComparison.OrdinalIgnoreCase))
        {
            return value.Substring(4);
        }
        return value;
    }

    private static bool IsSafeRequestId(string value)
    {
        if (String.IsNullOrWhiteSpace(value) || value.Length > 160) return false;
        for (int i = 0; i < value.Length; ++i)
        {
            char c = value[i];
            if (!(Char.IsLetterOrDigit(c) || c == '.' || c == '_' || c == '-' || c == ':')) return false;
        }
        return true;
    }

    private static ulong ProcessCreationTimeFileTime(Process process)
    {
        FileTime creation;
        FileTime exit;
        FileTime kernel;
        FileTime user;
        if (!GetProcessTimes(process.Handle, out creation, out exit, out kernel, out user))
            throw new InvalidOperationException(
                "GetProcessTimes failed with Win32 error "
                + Marshal.GetLastWin32Error().ToString(CultureInfo.InvariantCulture));
        ulong value = ((ulong)creation.High << 32) | creation.Low;
        if (value == 0)
            throw new InvalidOperationException("launcher process creation FILETIME is zero");
        return value;
    }

    private static Dictionary<string, object> BaseSuccess(string requestId, string operation)
    {
        Dictionary<string, object> result = new Dictionary<string, object>();
        result["schemaVersion"] = SchemaVersion;
        result["requestId"] = requestId;
        result["ok"] = true;
        result["operation"] = operation;
        return result;
    }

    private static string SerializeError(string requestId, string code, string message)
    {
        JavaScriptSerializer serializer = new JavaScriptSerializer();
        Dictionary<string, object> result = new Dictionary<string, object>();
        result["schemaVersion"] = SchemaVersion;
        result["requestId"] = requestId ?? "unknown";
        result["ok"] = false;
        result["errorCode"] = code;
        result["errorMessage"] = message;
        return serializer.Serialize(result);
    }

    private static string ExtractRequestId(string json)
    {
        try
        {
            JavaScriptSerializer serializer = new JavaScriptSerializer();
            IDictionary<string, object> request = serializer.DeserializeObject(json) as IDictionary<string, object>;
            if (request != null && request.ContainsKey("requestId")) return Convert.ToString(request["requestId"], CultureInfo.InvariantCulture);
        }
        catch { }
        return "unknown";
    }

    private static string GetString(IDictionary<string, object> map, string key)
    {
        object value;
        if (!map.TryGetValue(key, out value) || value == null) throw new InvalidOperationException(key + " is required");
        string text = value as string;
        if (text == null) throw new InvalidOperationException(key + " must be a string");
        return text;
    }

    private static int GetInt(IDictionary<string, object> map, string key)
    {
        object value;
        if (!map.TryGetValue(key, out value) || value == null) throw new InvalidOperationException(key + " is required");
        return Convert.ToInt32(value, CultureInfo.InvariantCulture);
    }

    private static List<string> GetStringList(IDictionary<string, object> map, string key)
    {
        object value;
        if (!map.TryGetValue(key, out value) || value == null) throw new InvalidOperationException(key + " is required");
        IEnumerable enumerable = value as IEnumerable;
        if (enumerable == null || value is string) throw new InvalidOperationException(key + " must be an array");
        List<string> result = new List<string>();
        int total = 0;
        foreach (object item in enumerable)
        {
            string text = item as string;
            if (text == null) throw new InvalidOperationException(key + " entries must be strings");
            total += text.Length;
            if (text.Length > 32768 || total > MaxMessageBytes) throw new InvalidOperationException(key + " is too large");
            result.Add(text);
        }
        if (result.Count > 512) throw new InvalidOperationException(key + " has too many entries");
        return result;
    }

    private static bool Contains(IList<string> args, string value)
    {
        for (int i = 0; i < args.Count; ++i) if (args[i] == value) return true;
        return false;
    }

    private static bool ContainsPair(IList<string> args, string name, string value)
    {
        for (int i = 0; i + 1 < args.Count; ++i)
            if (args[i] == name && args[i + 1] == value) return true;
        return false;
    }

    private static string ValueAfter(IList<string> args, string name)
    {
        for (int i = 0; i + 1 < args.Count; ++i) if (args[i] == name) return args[i + 1];
        return null;
    }

    private static string Sha256File(string path)
    {
        using (FileStream stream = File.OpenRead(path))
        using (SHA256 sha = SHA256.Create())
        {
            byte[] digest = sha.ComputeHash(stream);
            StringBuilder text = new StringBuilder(digest.Length * 2);
            for (int i = 0; i < digest.Length; ++i) text.Append(digest[i].ToString("x2", CultureInfo.InvariantCulture));
            return text.ToString();
        }
    }

    private static string JoinArguments(IList<string> args)
    {
        StringBuilder line = new StringBuilder();
        for (int i = 0; i < args.Count; ++i)
        {
            if (i != 0) line.Append(' ');
            line.Append(QuoteWindowsArgument(args[i]));
        }
        return line.ToString();
    }

    private static string QuoteWindowsArgument(string value)
    {
        if (value == null) value = String.Empty;
        bool needsQuotes = value.Length == 0;
        for (int i = 0; i < value.Length && !needsQuotes; ++i)
            needsQuotes = Char.IsWhiteSpace(value[i]) || value[i] == '"';
        if (!needsQuotes) return value;
        StringBuilder quoted = new StringBuilder();
        quoted.Append('"');
        int backslashes = 0;
        for (int i = 0; i < value.Length; ++i)
        {
            char c = value[i];
            if (c == '\\') { ++backslashes; continue; }
            if (c == '"')
            {
                quoted.Append('\\', backslashes * 2 + 1);
                quoted.Append('"');
                backslashes = 0;
                continue;
            }
            quoted.Append('\\', backslashes);
            backslashes = 0;
            quoted.Append(c);
        }
        quoted.Append('\\', backslashes * 2);
        quoted.Append('"');
        return quoted.ToString();
    }

    private static void WriteFrame(Stream stream, string text)
    {
        byte[] body = Encoding.UTF8.GetBytes(text);
        if (body.Length > MaxMessageBytes) throw new InvalidOperationException("broker message exceeds limit");
        byte[] length = BitConverter.GetBytes(body.Length);
        stream.Write(length, 0, length.Length);
        stream.Write(body, 0, body.Length);
        stream.Flush();
    }

    private static string ReadFrame(Stream stream)
    {
        byte[] lengthBytes = ReadExact(stream, 4);
        int length = BitConverter.ToInt32(lengthBytes, 0);
        if (length < 0 || length > MaxMessageBytes) throw new InvalidOperationException("invalid broker frame length");
        return Encoding.UTF8.GetString(ReadExact(stream, length));
    }

    private static byte[] ReadExact(Stream stream, int length)
    {
        byte[] result = new byte[length];
        int offset = 0;
        while (offset < length)
        {
            int read = stream.Read(result, offset, length - offset);
            if (read <= 0) throw new EndOfStreamException("broker pipe closed before frame completed");
            offset += read;
        }
        return result;
    }
}
