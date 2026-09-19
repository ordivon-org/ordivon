from ordivon_capital.market.private_reality import normalize_binance_observer, normalize_binance_usdm_observer, normalize_okx_observer


def call(data):
    return {'ok': True, 'response': {'data': data}}


def test_binance_observer_normalizes_without_inventing_execution_authority():
    env={
      'status':'success',
      'extensions':{
        'externalFinancialWriteAttempted':False,
        'credentialRestrictions':{
          'safe':True,
          'observed':{'enableReading':True,'enableSpotAndMarginTrading':False,'enableWithdrawals':False},
        },
      },
      'calls':{
        'account_get_account':call({'accountType':'SPOT','balances':[{'asset':'USDT','free':'10','locked':'2'}]}),
        'instrument:BTCUSDT:account_open_orders':call([{'orderId':1,'clientOrderId':'c1','symbol':'BTCUSDT','side':'BUY','type':'LIMIT','timeInForce':'GTC','status':'NEW','origQty':'0.1','executedQty':'0','price':'50000','updateTime':1}]),
        'instrument:BTCUSDT:account_all_orders':call([{'orderId':2,'clientOrderId':'c2','symbol':'BTCUSDT','side':'BUY','type':'MARKET','timeInForce':'IOC','status':'FILLED','origQty':'0.1','executedQty':'0.1','price':'0','updateTime':2}]),
        'instrument:BTCUSDT:account_my_trades':call([{'id':7,'orderId':2,'symbol':'BTCUSDT','qty':'0.1','price':'50010','commission':'0.0001','commissionAsset':'BTC','time':3}]),
      }
    }
    x=normalize_binance_observer(env)
    assert x['permissionStanding']=='READ_ONLY_VERIFIED'
    assert x['balances']==[{'asset':'USDT','available':'10','locked':'2','total':'12'}]
    assert x['openOrders'][0]['clientOrderId']=='c1'
    assert x['orderHistory'][0]['venueOrderId']=='2'
    assert x['fills'][0]['venueTradeId']=='7'
    assert x['externalFinancialWriteAttempted'] is False


def test_binance_trade_permission_fails_closed():
    env={'status':'failed','extensions':{'externalFinancialWriteAttempted':False,'credentialRestrictions':{'safe':False,'observed':{'enableReading':True,'enableSpotAndMarginTrading':True,'enableWithdrawals':False}}},'calls':{'account_get_account':call({'balances':[]})}}
    assert normalize_binance_observer(env)['permissionStanding']=='NOT_VERIFIED'


def okx_call(rows):
    return {'ok':True,'response':{'data':{'code':'0','msg':'','data':rows}}}


def test_okx_observer_normalizes_get_only_reality():
    env={'status':'success','externalFinancialWriteAttempted':False,'calls':{
      'config':okx_call([{'perm':'read_only'}]),
      'balance':okx_call([{'details':[{'ccy':'USDT','availBal':'90','eq':'100'}]}]),
      'positions':okx_call([{'instId':'BTC-USDT-SWAP','posId':'p1','posSide':'net','pos':'1','avgPx':'50000','markPx':'51000','uTime':'1'}]),
      'openOrders':okx_call([{'ordId':'o1','clOrdId':'c1','instId':'BTC-USDT-SWAP','side':'buy','ordType':'limit','state':'live','sz':'1','accFillSz':'0','px':'49000','uTime':'2'}]),
      'fills':okx_call([{'ordId':'o2','tradeId':'t1','instId':'BTC-USDT-SWAP','fillSz':'1','fillPx':'50000','fee':'-1','feeCcy':'USDT','fillTime':'3'}]),
    }}
    x=normalize_okx_observer(env)
    assert x['permissionStanding']=='READ_ONLY_VERIFIED'
    assert x['balances'][0]=={'asset':'USDT','available':'90','locked':'10','total':'100'}
    assert x['positions'][0]['instrumentId']=='BTC-USDT-SWAP'
    assert x['openOrders'][0]['clientOrderId']=='c1'
    assert x['fills'][0]['venueTradeId']=='t1'
    assert x['externalFinancialWriteAttempted'] is False


def test_binance_usdm_observer_preserves_provider_risk_truth_without_execution_authority():
    env={
      'standing':'READ_ONLY_PRIVATE_REALITY_CAPTURED',
      'externalFinancialWriteAttempted':False,
      'permissionGate':{'safe':True},
      'calls':{
        'account_information_v3':{'ok':True,'data':{
          'total_initial_margin':'10','total_maint_margin':'4','total_wallet_balance':'100',
          'total_unrealized_profit':'20','total_margin_balance':'120','available_balance':'80'}},
        'futures_account_balance_v3':{'ok':True,'data':[{
          'asset':'USDT','balance':'100','cross_wallet_balance':'100','cross_un_pnl':'20',
          'available_balance':'80','margin_available':True,'update_time':10}]},
        'futures_account_configuration':{'ok':True,'data':{'can_trade':True,'dual_side_position':False,'multi_assets_margin':False}},
        'get_current_multi_assets_mode':{'ok':True,'data':{'multi_assets_margin':False}},
        'get_current_position_mode':{'ok':True,'data':{'dual_side_position':False}},
        'notional_and_leverage_brackets':{'ok':True,'data':{'actual_instance':[{'symbol':'SNDKUSDT','brackets':[{'bracket':1,'initial_leverage':75,'notional_floor':'0','notional_cap':'1000','maint_margin_ratio':'0.01'}]}]}},
        'position_adl_quantile_estimation':{'ok':True,'data':{'symbol':'SNDKUSDT','adl_quantile':{'LONG':1,'SHORT':0}}},
        'position_information_v3':{'ok':True,'data':[{
          'symbol':'SNDKUSDT','position_side':'BOTH','position_amt':'0.1','entry_price':'1500',
          'break_even_price':'1502','mark_price':'1780','un_realized_profit':'28','liquidation_price':'1200',
          'notional':'178','margin_asset':'USDT','initial_margin':'35.6','maint_margin':'1.78',
          'position_initial_margin':'35.6','open_order_initial_margin':'0','adl':1,'update_time':20}]},
        'current_all_open_orders':{'ok':True,'data':[]},
        'account_trade_list':{'ok':True,'data':[{
          'id':1,'order_id':2,'symbol':'SNDKUSDT','side':'BUY','position_side':'BOTH',
          'qty':'0.1','price':'1500','commission':'0.05','commission_asset':'USDT',
          'realized_pnl':'0','time':30}]},
      }
    }
    x=normalize_binance_usdm_observer(env)
    assert x['permissionStanding']=='READ_ONLY_VERIFIED'
    assert x['product']=='USDⓈ-M_FUTURES'
    assert x['balances'][0]['total']=='100'
    assert x['positions'][0]['liquidationPx']=='1200'
    assert x['positions'][0]['maintenanceMargin']=='1.78'
    assert x['leverageBracket']['actual_instance'][0]['brackets'][0]['initial_leverage']==75
    assert x['tradFiAgreementStanding']=='UNKNOWN_NO_READ_ONLY_STATUS_API'
    assert x['tradeEligibilityStanding']=='NOT_INFERRED_FROM_READ_SURFACE'
    assert x['executionAdmitted'] is False
    assert x['externalFinancialWriteAttempted'] is False


def test_binance_usdm_observer_never_upgrades_unverified_permission():
    env={
      'standing':'PERMISSION_NOT_READ_ONLY',
      'externalFinancialWriteAttempted':False,
      'permissionGate':{'safe':False},
      'calls':{}
    }
    x=normalize_binance_usdm_observer(env)
    assert x['permissionStanding']=='NOT_VERIFIED'
    assert x['executionAdmitted'] is False
