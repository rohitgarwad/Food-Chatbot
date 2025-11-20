from fastapi import FastAPI, Request
from typing import Dict, Any

import db_helper
import generic_helper

app = FastAPI()

# --- Intent Handlers ---

in_progress_order = {}

def handle_new_order(parameters: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    if session_id in in_progress_order:
        del in_progress_order[session_id]

    fulfillment_text = ('Ok, starting a new order. You can say things like "I want two pizzas and one mango lassi".'
                        ' Make sure to specify a quantity for every food item! Also, we have only the following items'
                        ' on our menu: Pav Bhaji, Chole Bhature, Pizza, Mango Lassi, Masala Dosa, Biryani, Vada Pav,'
                        ' Rava Dosa, and Samosa.')
    return {
        "fulfillmentText": fulfillment_text
    }

def handle_order_add(parameters: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    items = parameters.get("food-item")
    quantities = parameters.get("number")

    if len(items) != len(quantities):
        fulfillment_text = "Sorry I didn't understand. Can you please specify food items and quantities clearly."
    else:
        new_order = dict(zip(items, quantities))

        if session_id in in_progress_order:
            current_order = in_progress_order[session_id]
            current_order.update(new_order)
            in_progress_order[session_id] = current_order
        else:
            in_progress_order[session_id] = new_order

        order_str = generic_helper.get_str_from_food_dict(in_progress_order[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return {
        "fulfillmentText": fulfillment_text
    }

def handle_order_remove(parameters: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    fulfillment_text = ''
    if session_id not in in_progress_order:
        return {
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order again?"
        }
    current_order = in_progress_order[session_id]
    food_items = parameters.get("food-item")

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {", ".join(removed_items)} from your order! '

    if len(no_such_items) > 0:
        fulfillment_text += f'Your current order does not contain {", ".join(no_such_items)}. '

    if len(current_order.keys()) == 0:
        fulfillment_text += f'Your current order is empty.'
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f"So far you have: {order_str}"

    return {
        "fulfillmentText": fulfillment_text
    }

def handle_order_complete(parameters: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    if session_id not in in_progress_order:
        fulfillment_text = "I'm having trouble finding your order. Sorry! Can you place a new order again?"
    else:
        order = in_progress_order[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                                "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order. " \
                                f"Here is your order ID: {order_id}. " \
                                f"Your order total is {order_total} which you can pay at the time of delivery."

        del in_progress_order[session_id]

    return {
        "fulfillmentText": fulfillment_text
    }

def save_to_db(order: Dict):
    next_order_id = db_helper.get_next_order_id()
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(food_item, int(quantity), next_order_id)
        if rcode == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id

def handle_track_order(parameters: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    order_id = int(parameters.get("number"))
    order_status = db_helper.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    return {
        "fulfillmentText": fulfillment_text
    }

# --- Webhook Endpoint ---

@app.post("/")
async def webhook_handler(request: Request):
    body = await request.json()
    query_result = body.get("queryResult", {})
    intent_name = query_result.get("intent", {}).get("displayName")
    parameters = query_result.get("parameters", {})
    output_contexts = query_result.get("outputContexts", [])
    session_id = generic_helper.extract_session_id(output_contexts[0].get("name"))

    intent_handlers = {
        "new.order": handle_new_order,
        "order.add - context: ongoing-order": handle_order_add,
        "order.remove - context: ongoing-order": handle_order_remove,
        "order.complete - context: ongoing-order": handle_order_complete,
        "track.order - context: ongoing-tracking": handle_track_order,
    }

    if intent_name in intent_handlers:
        return intent_handlers[intent_name](parameters, session_id)
    else:
        return {
            "fulfillmentText": f"Sorry, I don't understand the intent '{intent_name}'."
        }
