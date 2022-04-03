from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine, select, MetaData, Table
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only

from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

#These decorators allow you to use g.session to access the database inside the request code
@app.before_request
def create_session():
    g.session = scoped_session(DBSession) #g is an "application global" https://flask.palletsprojects.com/en/1.1.x/api/#application-globals

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    g.session.commit()
    g.session.remove()

"""
-------- Helper methods (feel free to add your own!) -------
"""

def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    #g.session.query(Log).all()
    g.session.add(json.dumps(d))
    g.session.commit()
    pass
def process_order(order):
    fields = ['sender_pk','receiver_pk','buy_currency','sell_currency','buy_amount','sell_amount']
    order_obj = Order(**{f:order[f] for f in fields})
    
    #print(order_obj)
    unfilled_db = g.session.query(Order).filter(Order.filled == None).all()
    g.session.add(order_obj)
    g.session.commit()
    """
    for existing_order in unfilled_db:       
        if existing_order.buy_currency == order_obj.sell_currency:
            if existing_order.sell_currency == order_obj.buy_currency:
                if (existing_order.sell_amount / existing_order.buy_amount) >= (order_obj.buy_amount/order_obj.sell_amount) :
                    
                    existing_order.filled = datetime.now()
                    order_obj.filled = datetime.now()
                    existing_order.counterparty_id = order_obj.id
                    #existing_order.counterparty = order_obj
                    order_obj.counterparty_id = existing_order.id
                    #order_obj.counterparty = existing_order
                    session.commit()
                    if (existing_order.buy_amount > order_obj.sell_amount) | (order_obj.buy_amount > existing_order.sell_amount) :
                        if (existing_order.buy_amount > order_obj.sell_amount):
                            parent = existing_order
                            counter = order_obj
                        if order_obj.buy_amount > existing_order.sell_amount:
                            parent = order_obj
                            counter = existing_order
                        child = {}
                        child['sender_pk'] = parent.sender_pk
                        child['receiver_pk'] = parent.receiver_pk
                        child['buy_currency'] = parent.buy_currency
                        child['sell_currency'] = parent.sell_currency
                        child['buy_amount'] = parent.buy_amount-counter.sell_amount
                        child['sell_amount'] = (parent.buy_amount-counter.sell_amount)*(parent.sell_amount/parent.buy_amount)  
                        child_obj = Order(**{f:child[f] for f in fields})
                        child_obj.creator_id = parent.id
                        session.add(child_obj)
                        
                        session.commit()
                        break
                    
                    break

    
    session.commit()
    """
    pass

def verify(content):
        sig = content.get('sig')
        payload = content.get('payload')
        #print(sig)
        #print(payload)
        platform = payload.get('platform')
        message = payload.get('message')
        pk = payload.get('pk')
        result = False
        if platform == "Ethereum":
        #print("Ethereum")
        #print(json.dumps(payload))
        #print(type(json.dumps(payload)))
            eth_encoded_msg = eth_account.messages.encode_defunct(text =json.dumps(payload))
        
            if eth_account.Account.recover_message(eth_encoded_msg,signature=sig) == pk:
                result = True
        elif platform == "Algorand":
            #algo_sig_str = algosdk.util.sign_bytes(payload.encode('utf-8'),algo_sk)
            algo_encoded_msg = json.dumps(payload).encode('utf-8')
            if algosdk.util.verify_bytes(algo_encoded_msg,sig,pk):
                result = True
        return result
"""
---------------- Endpoints ----------------
"""
    
@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform" ]
        fields = [ "sig", "payload" ]
        error = False
        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
        
        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                error = True
        if error:
            print( json.dumps(content) )
            log_message(content)
            return jsonify( False )
            
        #Your code here
        if verify(content):
            process_order(content.get('payload'))
        else: 
            log_message(content.get('payload'))
        #Note that you can access the database session using g.session

@app.route('/order_book')
def order_book():
    #Your code here
    db = g.session.query(Order).all()
    result = {'data' : db}
    #Note that you can access the database session using g.session
    return jsonify(result)

if __name__ == '__main__':
    app.run(port='5002')

