using System.Security.Cryptography;
using System.Text.Json;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Validation;

if (args.Length != 1)
{
    Console.Error.WriteLine("usage: ArtifactOpenXmlValidator <artifact.pptx|artifact.docx|artifact.xlsx>");
    return 2;
}

var path = Path.GetFullPath(args[0]);
if (!File.Exists(path))
{
    Console.Error.WriteLine($"artifact is absent: {path}");
    return 2;
}

static string Sha256(string path)
{
    using var stream = File.OpenRead(path);
    return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
}

static (OpenXmlPackage Package, string DocumentType) OpenPackage(string path)
{
    return Path.GetExtension(path).ToLowerInvariant() switch
    {
        ".pptx" => (PresentationDocument.Open(path, false), "presentation"),
        ".docx" => (WordprocessingDocument.Open(path, false), "wordprocessing"),
        ".xlsx" => (SpreadsheetDocument.Open(path, false), "spreadsheet"),
        var extension => throw new NotSupportedException($"unsupported Open XML artifact extension: {extension}")
    };
}

try
{
    var opened = OpenPackage(path);
    using var document = opened.Package;
    var validator = new OpenXmlValidator();
    var errors = validator.Validate(document)
        .Select(error => new
        {
            id = error.Id,
            errorType = error.ErrorType.ToString(),
            description = error.Description,
            partUri = error.Part?.Uri.ToString()
        })
        .ToArray();

    var result = new
    {
        status = errors.Length == 0 ? "PASS" : "FAIL",
        artifact = new
        {
            path,
            sha256 = Sha256(path),
            documentType = opened.DocumentType
        },
        validator = new
        {
            implementation = "DocumentFormat.OpenXml",
            packageVersion = "3.5.1",
            api = "OpenXmlValidator"
        },
        validationErrorCount = errors.Length,
        validationErrors = errors,
        boundary = "Open XML SDK validation-rule evidence for OOXML packages; business semantics, target Office behavior/rendering, visual/accessibility acceptance and destination delivery/read-back remain separate gates."
    };
    Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
    return errors.Length == 0 ? 0 : 1;
}
catch (Exception error)
{
    var result = new
    {
        status = "FAIL",
        artifact = new { path, sha256 = Sha256(path), documentType = Path.GetExtension(path).ToLowerInvariant() },
        validator = new { implementation = "DocumentFormat.OpenXml", packageVersion = "3.5.1", api = "OpenXmlValidator" },
        validationErrorCount = 1,
        validationErrors = new[] { new { id = "OPEN_EXCEPTION", errorType = error.GetType().Name, description = error.Message, partUri = (string?)null } }
    };
    Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
    return 1;
}
