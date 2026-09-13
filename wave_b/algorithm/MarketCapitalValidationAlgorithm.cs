using System.Text.Json;
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

    public override void Initialize()
    {
        SetStartDate(2013, 10, 7);
        SetEndDate(2013, 10, 11);
        SetCash(100000);
        SetBenchmark(_ => 0m);
        Settings.MinimumOrderMarginPortfolioPercentage = 0m;

        var path = Environment.GetEnvironmentVariable("MARKET_CAPITAL_TARGET_PORTFOLIO");
        if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
        {
            throw new InvalidOperationException("MARKET_CAPITAL_TARGET_PORTFOLIO must name one exact target portfolio artifact");
        }

        using var document = JsonDocument.Parse(File.ReadAllText(path));
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
            _arrivalPrices[target.Key] = Securities[target.Key].Price;
            SetHoldings(target.Key, target.Value);
        }
        _submitted = true;
        Debug("MC_TARGET_SUBMITTED");
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
