using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using QuickFix.FIX44;
using QuickFix.Fields;

if (args.Length != 2)
{
    Console.Error.WriteLine("usage: MarketCapital.Fix44Projector <input.json> <output.json>");
    return 2;
}

var inputPath = Path.GetFullPath(args[0]);
var outputPath = Path.GetFullPath(args[1]);
using var doc = JsonDocument.Parse(File.ReadAllBytes(inputPath));
var root = doc.RootElement;
if (root.GetProperty("kind").GetString() != "ordivon.capital.trading.fix44-projection-input")
    throw new InvalidOperationException("unexpected projection input kind");
if (root.GetProperty("purpose").GetString() != "MECHANICS_ONLY_NON_ECONOMIC")
    throw new InvalidOperationException("only mechanics-only non-economic projection is admitted");
if (root.GetProperty("networkSessionEnabled").GetBoolean())
    throw new InvalidOperationException("FIX projector must remain sessionless");
if (root.GetProperty("externalFinancialWritesAllowed").GetBoolean())
    throw new InvalidOperationException("FIX projector must not admit external writes");

var transactTime = DateTime.Parse(
    root.GetProperty("transactTimeUtc").GetString()!,
    System.Globalization.CultureInfo.InvariantCulture,
    System.Globalization.DateTimeStyles.AdjustToUniversal | System.Globalization.DateTimeStyles.AssumeUniversal);
var sender = root.GetProperty("senderCompId").GetString()!;
var evidenceSha = root.GetProperty("sourceEvidenceSha256").GetString()!;
if (evidenceSha.Length != 64 || evidenceSha.Any(c => !Uri.IsHexDigit(c)))
    throw new InvalidOperationException("invalid source evidence sha256");

var rows = new List<object>();
ulong seq = 0;
foreach (var x in root.GetProperty("intents").EnumerateArray())
{
    var clOrdId = x.GetProperty("clOrdId").GetString()!;
    var symbol = x.GetProperty("symbol").GetString()!;
    var destination = x.GetProperty("exDestination").GetString()!;
    var quantity = decimal.Parse(x.GetProperty("orderQty").GetString()!, System.Globalization.CultureInfo.InvariantCulture);
    var sideText = x.GetProperty("side").GetString()!;
    var tifText = x.GetProperty("timeInForce").GetString()!;
    if (quantity <= 0m) throw new InvalidOperationException("order quantity must be positive");
    var side = sideText switch { "BUY" => Side.BUY, "SELL" => Side.SELL, _ => throw new InvalidOperationException("unsupported side") };
    var tif = tifText switch { "IOC" => TimeInForce.IMMEDIATE_OR_CANCEL, "DAY" => TimeInForce.DAY, "GTC" => TimeInForce.GOOD_TILL_CANCEL, _ => throw new InvalidOperationException("unsupported TIF") };

    var message = new NewOrderSingle(
        new ClOrdID(clOrdId),
        new Symbol(symbol),
        new Side(side),
        new TransactTime(transactTime),
        new OrdType(OrdType.MARKET));
    message.OrderQty = new OrderQty(quantity);
    message.TimeInForce = new TimeInForce(tif);
    message.ExDestination = new ExDestination(destination);
    message.Header.SetField(new BeginString("FIX.4.4"));
    message.Header.SetField(new SenderCompID(sender));
    message.Header.SetField(new TargetCompID(destination + "_QUALIFICATION"));
    message.Header.SetField(new MsgSeqNum(++seq));
    message.Header.SetField(new SendingTime(transactTime));
    var raw = message.ToString();
    if (!raw.Contains("\u000135=D\u0001", StringComparison.Ordinal)) throw new InvalidOperationException("not NewOrderSingle");
    if (!raw.Contains("\u000140=1\u0001", StringComparison.Ordinal)) throw new InvalidOperationException("not Market order");
    if (!raw.Contains("\u000159=3\u0001", StringComparison.Ordinal)) throw new InvalidOperationException("not IOC");
    var digest = Convert.ToHexString(SHA256.HashData(Encoding.ASCII.GetBytes(raw))).ToLowerInvariant();
    rows.Add(new {
        protocol = "FIX.4.4",
        msgType = "D",
        clOrdId,
        symbol,
        side = side.ToString(),
        orderQty = quantity.ToString(System.Globalization.CultureInfo.InvariantCulture),
        ordType = OrdType.MARKET.ToString(),
        timeInForce = tif.ToString(),
        exDestination = destination,
        transactTimeUtc = transactTime.ToString("O"),
        rawSha256 = digest,
    });
}

var result = new {
    schemaVersion = 2,
    kind = "ordivon.capital.trading.fix44-projection-result",
    standing = "PASS_FIX44_NEW_ORDER_SINGLE_PROJECTION",
    purpose = "MECHANICS_ONLY_NON_ECONOMIC",
    fixLibrary = "QuickFIX/n 1.14.1",
    sourceEvidenceSha256 = evidenceSha,
    networkSessionEnabled = false,
    brokerCredentialsUsed = false,
    externalFinancialWritesAttempted = false,
    projectedIntents = rows,
};
Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);
File.WriteAllText(outputPath, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }) + "\n");
Console.WriteLine(JsonSerializer.Serialize(result));
return 0;
