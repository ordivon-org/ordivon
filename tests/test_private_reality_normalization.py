from market_capital.private_reality import normalize_binance_observer, normalize_okx_observer


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
