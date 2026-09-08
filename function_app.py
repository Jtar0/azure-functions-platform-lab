import azure.functions as func
import json
import logging

app = func.FunctionApp()


# ---------------------------------------------------------
# HTTP FUNCTION
# Simple endpoint used to verify the Function App is live.
# ---------------------------------------------------------

@app.route(route="howdy", auth_level=func.AuthLevel.FUNCTION)
def howdy(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Howdy HTTP function received a request.")

    name = req.params.get("name")

    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = None

        if req_body:
            name = req_body.get("name")

    if name:
        return func.HttpResponse(
            f"Howdy, {name}! Deployed automatically through GitHub Actions.",
            status_code=200
        )

    return func.HttpResponse(
        "Howdy! Pass a name in the query string for a personalized response.",
        status_code=200
    )


# ---------------------------------------------------------
# FOOD TRUCK TRANSACTION PROCESSOR
#
# Triggered automatically when a new transaction JSON file
# is uploaded to the "uploads" Blob Storage container.
# ---------------------------------------------------------

@app.blob_trigger(
    arg_name="myblob",
    path="uploads/{name}",
    connection="AzureWebJobsStorage"
)
def process_upload(myblob: func.InputStream):

    logging.info(
        f"New food truck transaction received: {myblob.name}"
    )

    try:
        # Read the uploaded blob and parse the JSON.
        transaction = json.loads(
            myblob.read().decode("utf-8")
        )

        # Required transaction fields.
        transaction_id = transaction["transaction_id"]
        truck_id = transaction["truck_id"]
        amount = float(transaction["amount"])
        payment_type = transaction["payment_type"]

        # Optional promo code.
        promo_code = transaction.get("promo_code")

        # Basic validation.
        if amount <= 0:
            raise ValueError(
                "Transaction amount must be greater than zero"
            )

        # Save original price before discounts.
        original_amount = amount
        discount = 0.0

        # Hypothetical Sandia Sweets promo.
        if promo_code == "505CANDY":
            discount = round(amount * 0.10, 2)
            amount = round(amount - discount, 2)

        # Hypothetical 2% platform fee calculated
        # after any promotional discount.
        platform_fee = round(amount * 0.02, 2)
        truck_proceeds = round(amount - platform_fee, 2)

        # Log successfully processed transaction.
        logging.info(
            f"TRANSACTION PROCESSED | "
            f"ID: {transaction_id} | "
            f"Truck: {truck_id} | "
            f"Payment: {payment_type} | "
            f"Original: ${original_amount:.2f} | "
            f"Promo: {promo_code or 'NONE'} | "
            f"Discount: ${discount:.2f} | "
            f"Charged: ${amount:.2f} | "
            f"Platform Fee: ${platform_fee:.2f} | "
            f"Truck Proceeds: ${truck_proceeds:.2f}"
        )

    except (KeyError, ValueError, json.JSONDecodeError) as error:

        logging.error(
            f"TRANSACTION REJECTED | "
            f"Blob: {myblob.name} | "
            f"Reason: {error}"
        )
