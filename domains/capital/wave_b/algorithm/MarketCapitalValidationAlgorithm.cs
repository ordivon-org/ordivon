using System.Text.Json;
using System.Security.Cryptography;
using System.Reflection;
using System.Runtime.Loader;
using System.Text;
using QuickFix.FIX44;
using QfBeginString = QuickFix.Fields.BeginString;
using QfClOrdID = QuickFix.Fields.ClOrdID;
using QfMsgSeqNum = QuickFix.Fields.MsgSeqNum;
using QfOrdType = QuickFix.Fields.OrdType;
using QfOrderQty = QuickFix.Fields.OrderQty;
using QfSenderCompID = QuickFix.Fields.SenderCompID;
using QfSendingTime = QuickFix.Fields.SendingTime;
using QfSide = QuickFix.Fields.Side;
using QfSymbol = QuickFix.Fields.Symbol;
using QfTargetCompID = QuickFix.Fields.TargetCompID;
using QfTimeInForce = QuickFix.Fields.TimeInForce;
using QfTransactTime = QuickFix.Fields.TransactTime;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Data;
using QuantConnect.Orders;
using QuantConnect.Orders.Slippage;

namespace OrdivonMarketCapital;

public sealed class MarketCapitalValidationAlgorithm : QCAlgorithm
{
    private readonly Dictionary<Symbol, decimal> _targets = new();
    private readonly Dictionary<Symbol, decimal> _arrivalPrices = new();
    private bool _submitted;
    private bool _fixIntentEnabled;
    private string _targetPortfolioSha256 = string.Empty;
    private int _fixSequence;

    public override void Initialize()
    {
        var startText = Environment.GetEnvironmentVariable("MARKET_CAPITAL_BACKTEST_START") ?? "2013-10-07";
        var endText = Environment.GetEnvironmentVariable("MARKET_CAPITAL_BACKTEST_END") ?? "2013-10-11";
        var start = DateTime.ParseExact(startText, "yyyy-MM-dd", System.Globalization.CultureInfo.InvariantCulture);
        var end = DateTime.ParseExact(endText, "yyyy-MM-dd", System.Globalization.CultureInfo.InvariantCulture);
        if (end < start) throw new InvalidOperationException("backtest end precedes start");
        SetStartDate(start.Year, start.Month, start.Day);
        SetEndDate(end.Year, end.Month, end.Day);
        SetCash(100000);
        SetBenchmark(_ => 0m);
        Settings.MinimumOrderMarginPortfolioPercentage = 0m;
        var executionBufferText = Environment.GetEnvironmentVariable("MARKET_CAPITAL_EXECUTION_CASH_BUFFER_WEIGHT") ?? "0.01";
        if (!decimal.TryParse(executionBufferText, System.Globalization.NumberStyles.Number, System.Globalization.CultureInfo.InvariantCulture, out var executionBuffer) || executionBuffer < 0m || executionBuffer >= 1m)
        {
            throw new InvalidOperationException("invalid MARKET_CAPITAL_EXECUTION_CASH_BUFFER_WEIGHT");
        }
        Settings.FreePortfolioValuePercentage = executionBuffer;
        Debug($"MC_FEASIBILITY_POLICY|freePortfolioValuePercentage={executionBuffer}");

        var path = Environment.GetEnvironmentVariable("MARKET_CAPITAL_TARGET_PORTFOLIO");
        if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
        {
            throw new InvalidOperationException("MARKET_CAPITAL_TARGET_PORTFOLIO must name one exact target portfolio artifact");
        }

        var targetBytes = File.ReadAllBytes(path);
        _targetPortfolioSha256 = Convert.ToHexString(SHA256.HashData(targetBytes)).ToLowerInvariant();
        _fixIntentEnabled = string.Equals(Environment.GetEnvironmentVariable("MARKET_CAPITAL_FIX_INTENT_ENABLED"), "true", StringComparison.OrdinalIgnoreCase);
        if (_fixIntentEnabled) EnsureQuickFixAssemblyResolution();
        using var document = JsonDocument.Parse(targetBytes);
        var root = document.RootElement;
        if (root.GetProperty("method").GetString() != "equal_weight_validation_research_gated")
        {
            throw new InvalidOperationException("Wave B M1 accepts only the Wave A research-gated validation portfolio");
        }

        foreach (var position in root.GetProperty("positions").EnumerateArray())
        {
            var ticker = position.GetProperty("symbol").GetString() ?? throw new InvalidOperationException("symbol missing");
            var weight = position.GetProperty("target_weight").GetDecimal();
            if (weight <= 0m || weight > 1m) throw new InvalidOperationException($"invalid target weight for {ticker}");
            var security = AddEquity(ticker, Resolution.Daily, dataNormalizationMode: DataNormalizationMode.Raw);
            security.SetSlippageModel(new VolumeShareSlippageModel(0.30m, 0.05m));
            _targets.Add(security.Symbol, weight);
            Debug($"MC_EXECUTION_MODEL|symbol={ticker}|feeModel={security.FeeModel.GetType().Name}|slippageModel={security.SlippageModel.GetType().Name}|fillModel={security.FillModel.GetType().Name}");
        }

        var total = _targets.Values.Sum();
        if (Math.Abs(total - 1m) > 0.000001m) throw new InvalidOperationException($"target weights sum to {total}");
        Debug($"MC_TARGET_ADMITTED|path={path}|symbols={string.Join(',', _targets.Keys.Select(x => x.Value))}|weightSum={total}");
    }

    public override void OnData(Slice slice)
    {
        if (_submitted || _targets.Keys.Any(symbol => Securities[symbol].Price <= 0m)) return;
        foreach (var target in _targets)
        {
            var arrivalPrice = Securities[target.Key].Price;
            _arrivalPrices[target.Key] = arrivalPrice;
            var quantity = CalculateOrderQuantity(target.Key, target.Value);
            if (quantity == 0m) throw new InvalidOperationException($"LEAN produced zero feasible quantity for {target.Key.Value}");
            Debug($"MC_PRETRADE_QUANTITY|symbol={target.Key.Value}|targetWeight={target.Value}|arrivalPrice={arrivalPrice}|quantity={quantity}|estimatedNotional={quantity * arrivalPrice}|freePortfolioValue={Portfolio.TotalPortfolioValue * Settings.FreePortfolioValuePercentage}");
            string? clOrdId = null;
            if (_fixIntentEnabled)
            {
                clOrdId = EmitFix44NewOrderSingle(target.Key, quantity);
            }
            var ticket = MarketOrder(target.Key, quantity, tag: clOrdId is null ? null : $"FIX44:{clOrdId}");
            if (clOrdId is not null)
            {
                Debug($"MC_FIX_EXECUTION_LINK|clOrdId={clOrdId}|leanOrderId={ticket.OrderId}|symbol={target.Key.Value}|quantity={quantity}");
            }
        }
        _submitted = true;
        Debug("MC_FEASIBLE_ORDER_SET_SUBMITTED");
    }

    private static void EnsureQuickFixAssemblyResolution()
    {
        var directory = Environment.GetEnvironmentVariable("MARKET_CAPITAL_FIX_ASSEMBLY_DIRECTORY");
        if (string.IsNullOrWhiteSpace(directory) || !Directory.Exists(directory))
            throw new InvalidOperationException("MARKET_CAPITAL_FIX_ASSEMBLY_DIRECTORY is unavailable");
        AssemblyLoadContext.Default.Resolving += (context, name) =>
        {
            if (name.Name is not ("QuickFix" or "QuickFix.FIX44" or "Microsoft.Extensions.Logging.Abstractions" or "Microsoft.Extensions.DependencyInjection.Abstractions")) return null;
            var candidate = Path.Combine(directory, name.Name + ".dll");
            return File.Exists(candidate) ? context.LoadFromAssemblyPath(candidate) : null;
        };
    }

    private string EmitFix44NewOrderSingle(Symbol symbol, decimal signedQuantity)
    {
        var side = signedQuantity > 0m ? QfSide.BUY : QfSide.SELL;
        var orderQty = Math.Abs(signedQuantity);
        var idSeed = $"{_targetPortfolioSha256}|{Time:yyyy-MM-ddTHH:mm:ss}|{symbol.Value}|{signedQuantity.ToString(System.Globalization.CultureInfo.InvariantCulture)}";
        var clOrdId = "mc_" + Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(idSeed))).ToLowerInvariant()[..24];
        var utc = Time.Kind == DateTimeKind.Utc ? Time : DateTime.SpecifyKind(Time, DateTimeKind.Utc);
        var message = new NewOrderSingle(
            new QfClOrdID(clOrdId),
            new QfSymbol(symbol.Value),
            new QfSide(side),
            new QfTransactTime(utc),
            new QfOrdType(QfOrdType.MARKET));
        message.OrderQty = new QfOrderQty(orderQty);
        message.TimeInForce = new QfTimeInForce(QfTimeInForce.DAY);
        message.Header.SetField(new QfBeginString("FIX.4.4"));
        message.Header.SetField(new QfSenderCompID("ORDIVON_SHADOW"));
        message.Header.SetField(new QfTargetCompID("LEAN_VALIDATION"));
        message.Header.SetField(new QfMsgSeqNum((ulong)++_fixSequence));
        message.Header.SetField(new QfSendingTime(utc));
        var raw = message.ToString();
        if (!raw.Contains("\u000135=D\u0001", StringComparison.Ordinal) || !raw.Contains("\u000140=1\u0001", StringComparison.Ordinal))
            throw new InvalidOperationException("QuickFIX/n did not serialize the required FIX 4.4 NewOrderSingle market-order semantics");
        var digest = Convert.ToHexString(SHA256.HashData(Encoding.ASCII.GetBytes(raw))).ToLowerInvariant();
        Debug($"MC_FIX_INTENT|protocol=FIX.4.4|msgType=D|clOrdId={clOrdId}|symbol={symbol.Value}|side={side}|orderQty={orderQty}|ordType={QfOrdType.MARKET}|timeInForce={QfTimeInForce.DAY}|sha256={digest}");
        return clOrdId;
    }

    public override void OnOrderEvent(OrderEvent orderEvent)
    {
        var arrival = _arrivalPrices.TryGetValue(orderEvent.Symbol, out var price) ? price : 0m;
        var delta = orderEvent.FillPrice == 0m || arrival == 0m ? 0m : orderEvent.FillPrice - arrival;
        Debug($"MC_ORDER_EVENT|id={orderEvent.OrderId}|symbol={orderEvent.Symbol.Value}|status={orderEvent.Status}|fillQty={orderEvent.FillQuantity}|fillPrice={orderEvent.FillPrice}|arrivalPrice={arrival}|executionPriceDelta={delta}|fee={orderEvent.OrderFee.Value.Amount}");
    }

    public override void OnEndOfAlgorithm()
    {
        foreach (var target in _targets)
        {
            var holding = Portfolio[target.Key];
            var actualWeight = Portfolio.TotalPortfolioValue == 0m ? 0m : holding.HoldingsValue / Portfolio.TotalPortfolioValue;
            Debug($"MC_FINAL_HOLDING|symbol={target.Key.Value}|quantity={holding.Quantity}|price={holding.Price}|value={holding.HoldingsValue}|targetWeight={target.Value}|actualWeight={actualWeight}");
        }
        Debug($"MC_FINAL_PORTFOLIO|totalValue={Portfolio.TotalPortfolioValue}|cash={Portfolio.Cash}|marginUsed={Portfolio.TotalMarginUsed}");
    }
}
