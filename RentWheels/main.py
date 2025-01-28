import os
import re
from bson import ObjectId
from flask import Flask, request, render_template, redirect, session, app
from datetime import datetime
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT_CAR = APP_ROOT + "/static/added_cars"

import pymongo

app = Flask(__name__)
parking_slot = pymongo.MongoClient("mongodb://localhost:27017/")
my_database = parking_slot["car_rental_management"]
admin_collection = my_database["admin"]
car_owner_collection = my_database["car_owner"]
location_collection = my_database["location"]
vehicle_collection = my_database["vehicle"]
customer_collection = my_database["customer"]
booking_collection = my_database["booking"]
payment_collection = my_database["payment"]
review_collection = my_database["review"]

app.secret_key = "car_rental_management"

query = {}
count = admin_collection.count_documents({})
if count == 0:
    query = {"username": "admin", "password": "admin"}
    admin_collection.insert_one(query)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")

@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    username = request.form.get("username")
    password = request.form.get("password")
    query = {"username": username, "password": password}
    count = admin_collection.count_documents(query)
    if count > 0:
        admin = admin_collection.find_one(query)
        session["admin_id"] = str(admin['_id'])
        session["role"] = 'admin'
        return redirect("/admin_home")
    else:
        return render_template("message.html", message="invalid login details")


@app.route("/car_owner_login")
def car_owner_login():
    locations = location_collection.find()
    return render_template("car_owner_login.html", locations=locations)


@app.route("/car_owner_login_action", methods=["POST"])
def car_owner_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = car_owner_collection.count_documents(query)
    if count > 0:
        car_owner = car_owner_collection.find_one(query)
        if car_owner["status"] == 'Not Verified':
            return render_template("message.html", message="Your Account Not Verified")
        else:
            car_owner = car_owner_collection.find_one(query)
            session['car_owner_id'] = str(car_owner['_id'])
            session['role'] = "car_owner"
            return redirect("/car_owner_home")
    else:
        return render_template("message.html", message="Invalid Login Details")


@app.route("/car_owner_registration_action", methods=["POST"])
def car_owner_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email_1")
    password = request.form.get("password_1")
    phone = request.form.get("phone")
    city = request.form.get("city")
    ssn = request.form.get("ssn")
    zip_code = request.form.get("zip_code")
    location_id = request.form.get("location_id")
    license_number = request.form.get("license_number")
    state = request.form.get("state")
    query = {"$or": [{"email": email}, {"password": password}]}
    count = car_owner_collection.count_documents(query)
    if count == 0:
        query = {"first_name": first_name, "last_name": last_name, "email": email, "password": password, "phone": phone,
                 "location_id": ObjectId(location_id),"ssn":ssn,"license_number":license_number,
                 "state": state, "city": city, "zip_code": zip_code, "status": 'Not Verified'}
        car_owner_collection.insert_one(query)
        return render_template("message.html", message="Car Owner Registered Successfully")
    else:
        return render_template("message.html", message="Duplicate Details Entered")


@app.route("/customer_login")
def customer_login():
    locations = location_collection.find()
    return render_template("customer_login.html", locations=locations)


@app.route("/customer_registration_action", methods=["post"])
def customer_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email_1")
    password = request.form.get("password_1")
    phone = request.form.get("phone")
    state = request.form.get("state")
    city = request.form.get("city")
    address = request.form.get("address")
    zip_code = request.form.get("zip_code")
    license_number = request.form.get("license_number")
    location_id = request.form.get("location_id")
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = customer_collection.count_documents(query)
    if count == 0:
        query = {"first_name": first_name, "last_name": last_name, "email": email, "password": password, "phone": phone,
                 "state": state, "city": city, "address": address,
                 "zip_code": zip_code, "license_number": license_number, "location_id": ObjectId(location_id)}
        customer_collection.insert_one(query)
        return render_template("message.html", message="Customer Registered Successfully")
    else:
        return render_template("message.html", message="Duplicate Entry")


@app.route("/customer_login_action",methods=['post'])
def customer_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"email": email, "password": password}
    count = customer_collection.count_documents(query)
    if count > 0:
        customer = customer_collection.find_one(query)
        session['customer_id'] = str(customer['_id'])
        session['role'] = "customer"
        return redirect("/customer_home")
    else:
        return render_template("message.html", message="Invalid Login Details")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/add_view_locations")
def add_view_locations():
    locations = location_collection.find()
    return render_template("add_view_locations.html", locations=locations)


@app.route("/add_location_action")
def add_location_action():
    location_name = request.args.get("location_name")
    query = {"$or": [{"location_name": location_name}]}
    count = location_collection.count_documents(query)
    if count == 0:
        query = {"location_name": location_name}
        location_collection.insert_one(query)
        return redirect("/add_view_locations")
    else:
        return render_template("message_action.html", message="Duplicat Location Exist")


@app.route("/view_verify_car_owners")
def view_verify_car_owners():
    car_owners = car_owner_collection.find()
    return render_template("view_verify_car_owners.html", car_owners=car_owners, get_location_by_location_id=get_location_by_location_id)


def get_location_by_location_id(location_id):
    query = {"_id": location_id}
    location = location_collection.find_one(query)
    return location

# # trial
# def get_paymentinfo_by_customer_id(customer_id):
#     query = {"_id": customer_id}
#     payment = payment_collection.find_one(query)
#     return payment


@app.route("/verify_car_owner")
def verify_car_owner():
    car_owner_id = request.args.get("car_owner_id")
    query1 = {"_id": ObjectId(car_owner_id)}
    query2 = {"$set": {"status": "Verified"}}
    car_owner_collection.update_one(query1, query2)
    return redirect("/view_verify_car_owners")


@app.route("/de_verify_car_owner")
def de_verify_car_owner():
    car_owner_id = request.args.get("car_owner_id")
    query1 = {"_id": ObjectId(car_owner_id)}
    query2 = {"$set": {"status": "Not Verified"}}
    car_owner_collection.update_one(query1, query2)
    return redirect("/view_verify_car_owners")


@app.route("/approve_cars")
def approve_cars():
    vehicle_id = request.args.get("vehicle_id")
    query1 = {"_id": ObjectId(vehicle_id)}
    query2 = {"$set": {"status": "Approved"}}
    vehicle_collection.update_one(query1, query2)
    return redirect("/view_vehicles")





@app.route("/car_owner_home")
def car_owner_home():
    return render_template("car_owner_home.html")


@app.route("/add_vehicles")
def add_vehicles():
    car_owner = car_owner_collection.find_one({"_id":ObjectId(session['car_owner_id'])})
    return render_template("add_vehicles.html",car_owner=car_owner,get_location_by_id=get_location_by_id)

def get_location_by_id(location_id):
    location = location_collection.find_one({"_id":ObjectId(location_id)})
    return location


@app.route("/add_vehicle_actions", methods=["post"])
def add_vehicle_actions():
    vehicle_name = request.form.get("vehicle_name")
    vin_number = request.form.get("vin_number")
    make = request.form.get("make")
    model = request.form.get("model")
    year = request.form.get("year")
    security_deposit = request.form.get("security_deposit")
    rent_per_day = request.form.get("rent_per_day")
    ev_gas_levels = request.form.get("ev_gas_levels")
    car_mileage = request.form.get("car_mileage")
    color = request.form.get("color")
    insurance = request.form.get("insurance")
    mile_per_price = request.form.get("mile_per_price")
    image = request.files.get("image")
    path = APP_ROOT_CAR + "/" + image.filename
    image.save(path)
    location_id = request.form.get("location_id")
    car_owner_id = session['car_owner_id']
    query = {"vehicle_name": vehicle_name, "vin_number": vin_number, "make": make,"color":color,"car_mileage":car_mileage,
             "model": model, "year": year, "security_deposit": security_deposit,
             "rent_per_day": rent_per_day, "ev_gas_levels": ev_gas_levels,
             "insurance": insurance, "mile_per_price": mile_per_price,
             "car_owner_id": ObjectId(car_owner_id), "image": image.filename, "status": 'Not Approved',"location_id":ObjectId(location_id)}
    vehicle_collection.insert_one(query)

    return render_template("message_action.html", message="Vehicle Added Successfully")


@app.route("/view_vehicles")
def view_vehicles():
    query = {}
    if session['role']=='car_owner':
        car_owner_id = session['car_owner_id']
        query = {"car_owner_id":ObjectId(car_owner_id)}
    elif session['role']=='admin':
        query = {}
    cars = vehicle_collection.find(query)
    return render_template("view_vehicles.html", cars=cars,get_location_by_id=get_location_by_id)


@app.route("/view_book_vehicles")
def view_book_vehicles():
    searchInput = request.args.get("searchInput")
    car_owner_id = request.args.get("car_owner_id")
    query = {}
    if car_owner_id == None and searchInput == None :
        car_owner_id = ""
    if searchInput == None :
        searchInput = ""

    if car_owner_id!="" and searchInput =="":
        query = {"car_owner_id": ObjectId(car_owner_id)}
    elif car_owner_id=="" and searchInput!="":
        customer = customer_collection.find_one({"_id":ObjectId(session['customer_id'])})
        query = {"searchInput":searchInput,"location_id":ObjectId(customer['location_id'])}
    else:
        customer = customer_collection.find_one({"_id":ObjectId(session['customer_id'])})
        query = {"location_id":ObjectId(customer['location_id'])}

    cars = vehicle_collection.find(query)
    car_owners = car_owner_collection.find({})
    return render_template("view_book_vehicles.html", cars=cars, car_owners=car_owners,get_location_by_id=get_location_by_id)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/customer_home")
def customer_home():
    return render_template("customer_home.html")


@app.route("/book_cars")
def book_cars():
    car_owner_id = request.args.get("car_owner_id")
    vehicle_id = request.args.get("vehicle_id")
    rent_per_day = request.args.get("rent_per_day")
    insurance_amount = request.args.get("insurance_amount")
    from_date_time = request.args.get("from_date_time")
    to_date_time = request.args.get("to_date_time")
    ev_gas_levels = request.args.get("ev_gas_levels")
    return render_template("book_cars.html",vehicle_id=vehicle_id,rent_per_day=rent_per_day,insurance_amount=insurance_amount,from_date_time=from_date_time,to_date_time=to_date_time,ev_gas_levels=ev_gas_levels,car_owner_id=car_owner_id)


@app.route("/book_insurance_action")
def book_insurance_action():
    car_owner_id = request.args.get("car_owner_id")
    ev_gas_levels = request.args.get("ev_gas_levels")
    vehicle_id = request.args.get("vehicle_id")
    rent_per_day = request.args.get("rent_per_day")
    insurance_amount = request.args.get("insurance_amount")
    insurance = request.args.get("insurance")
    if insurance == "Required":
        insurance = insurance_amount
    else:
        insurance = 0
    start_date_time1 = request.args.get("from_date_time")
    end_date_date1 = request.args.get("to_date_time")
    start_date_time = datetime.strptime(start_date_time1, "%Y-%m-%d")
    end_date_time = datetime.strptime(end_date_date1, '%Y-%m-%d')
    start_date_time3 = datetime.strptime(start_date_time1, "%Y-%m-%d")
    end_date_date3 = datetime.strptime(end_date_date1, '%Y-%m-%d')
    query = {"$or": [{"start_date_time": {"$gte": start_date_time3, "$lte": end_date_date3},
                      "end_date_date": {"$gte": start_date_time3, "$gte": end_date_date3},
                      "status": {"$in": ['Requested', 'Booked','Handover To Customer' 'Request Accepted']}},
                     {"start_date_time": {"$lte": start_date_time3, "$lte": end_date_date3},
                      "end_date_date": {"$gte": start_date_time3, "$lte": end_date_date3},
                      "status": {"$in": ['Requested','Booked', 'Handover To Customer', 'Request Accepted']}},
                     {"start_date_time": {"$lte": start_date_time3, "$lte": end_date_date3},
                      "end_date_date": {"$gte": start_date_time3, "$gte": end_date_date3},
                      "status": {"$in": ['Requested', 'Booked','Handover To Customer', 'Request Accepted']}},
                     {"start_date_time": {"$gte": start_date_time3, "$lte": end_date_date3},
                      "end_date_date": {"$gte": start_date_time3, "$lte": end_date_date3},
                      "status": {"$in": ['Requested', 'Booked','Handover To Customer', 'Request Accepted']}},
                     ],"vehicle_id":ObjectId(vehicle_id)}
    count = booking_collection.count_documents(query)
    if count>0:
        return render_template("message_action.html", message="Car Not Available On These dates")

    diff = end_date_time - start_date_time
    days = diff.days
    print(days)
    vehicle = vehicle_collection.find_one({"_id": ObjectId(vehicle_id)})
    totalPrice = int(vehicle['rent_per_day']) * int(days)
    admin_commission = int(totalPrice) * 0.1
    admin_commission_str = str(admin_commission)
    print(totalPrice)
    amount = int(totalPrice) * float(0.2)
    print(amount)

    booking_collection.insert_one(
        {"vehicle_id": ObjectId(vehicle_id), "start_date_time": start_date_time3, "end_date_date": end_date_date3,
         "admin_commission": admin_commission_str,"insurance":insurance,
         "total_amount": totalPrice, "booking_date": datetime.now(), "status": 'Requested',
         "ev_gas_levels": ev_gas_levels,"days":days,
         "customer_id": ObjectId(session['customer_id']), "car_owner_id": ObjectId(car_owner_id)})
    return render_template("message_action.html",message="Booking Requested")


@app.route("/payment")
def payment():
    booking_id = request.args.get("booking_id")
    booking = booking_collection.find_one({"_id": ObjectId(booking_id)})
    booking2 = booking_collection.find_one({"_id": ObjectId(booking_id)})
    total_amount = booking2['total_amount']
    advance_pay = float(total_amount)*20/100 #float(total_amount)-float(total_amount)*20/100
    vehicle = vehicle_collection.find_one()
    return render_template("payment.html",booking_id=booking_id,vehicle=vehicle,booking=booking,float=float,advance_pay=advance_pay)


@app.route("/advance_payment_action")
def advance_payment_action():
    booking_id = request.args.get("booking_id")
    amount = request.args.get("amount")
    expiry_date = request.args.get("expiry_date")
    card_number = request.args.get("card_number")
    card_type = request.args.get("card_type")
    card_holder_name = request.args.get("card_holder_name")
    cvv = request.args.get("cvv")

    payment_collection.insert_one(
        {"booking_id": ObjectId(booking_id), "customer_id": ObjectId(session['customer_id']), "card_type": card_type,
         "card_holder_name": card_holder_name, "expiry_date": expiry_date, "card_number": card_number, "cvv": cvv,
         "status": 'Advance Payment Successfully', "payment_amount": amount,"payment_date": datetime.now()})
    query = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "Booked"}}
    booking_collection.update_one(query, query2)
    return render_template("message_action.html", message="Car Booked Successfully")


@app.route("/view_bookings")
def view_bookings():
    query = {}
    if session['role']=='customer':
        query = {"customer_id":ObjectId(session['customer_id'])}
    elif session['role']=='car_owner':
        cars = vehicle_collection.find({"car_owner_id":ObjectId(session['car_owner_id'])})
        carIds = []
        for car in cars:
            carIds.append({"vehicle_id":ObjectId(car['_id'])})
        query = {"$or":carIds}
        print(query)
    bookings = booking_collection.find(query)
    bookings = list(bookings)
    return render_template("/view_bookings.html", bookings=bookings,is_paid_by_customer=is_paid_by_customer,get_car_owner_by_car_owner_id=get_car_owner_by_car_owner_id,
                           get_customer_by_customer_id=get_customer_by_customer_id, get_car_by_car_id=get_car_by_car_id,int=int,get_total_payment=get_total_payment)



def get_customer_by_customer_id(customer_id):
    query = {"_id": customer_id}
    customer = customer_collection.find_one(query)
    return customer


def get_car_owner_by_car_owner_id(car_owner_id):
    query = {"_id": car_owner_id}
    car_owner = car_owner_collection.find_one(query)
    return car_owner


def get_car_by_car_id(vehicle_id):
    query = {"_id": vehicle_id}
    car = vehicle_collection.find_one(query)
    return car


def is_paid_by_customer(booking_id):
    query={"booking_id":ObjectId(booking_id)}
    count = booking_collection.count_documents(query)
    print(count)
    if count > 0:
        return False
    else:
        return True


def get_total_payment(booking_id):
    booking = booking_collection.find_one({"_id":ObjectId(booking_id)})
    print(booking)
    car_id = booking['vehicle_id']
    car = vehicle_collection.find_one({"_id":ObjectId(car_id)})
    amount = booking['amount']
    remaing_amount = float(amount)*float(0.8)
    damage_amount = 0
    extra_charges = 0
    if booking['damage']=='No Damage':
        damage_amount = 0
    else:
        damage_amount = car['extra_charges']
    if int(booking['extra_charges'])>0:
        extra_charges = booking['extra_charges']
    total_payment = int(damage_amount)+int(extra_charges)
    print(total_payment)
    total_payment2 = total_payment+remaing_amount
    return total_payment2


@app.route("/accept_booking_action")
def accept_booking_action():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "Request Accepted"}}
    booking_collection.update_one(query, query2)
    return redirect("view_bookings")


@app.route("/reject_booking_action")
def reject_booking_action():
    booking_id = request.args.get("booking_id")
    return render_template("reason.html",booking_id=booking_id)


@app.route("/submit_reject_reason")
def submit_reject_reason():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    reason= request.args.get("reason")
    query2 = {"$set": {"status": "Request Rejected","reason":reason}}
    booking_collection.update_one(query, query2)
    return redirect("/view_bookings")


@app.route("/return_request_action")
def return_request_action():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "Return Requested"}}
    booking_collection.update_one(query, query2)
    return redirect("view_bookings")


@app.route("/handover_to_customer")
def handover_to_customer():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "Handover To Customer"}}
    booking_collection.update_one(query, query2)
    return redirect("view_bookings")


@app.route("/drop_customer_action")
def drop_customer_action():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "Drop Customer"}}
    booking_collection.update_one(query, query2)
    return redirect("view_bookings")


@app.route("/verified")
def verified():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "verified  "}}
    booking_collection.update_one(query, query2)
    return redirect("view_bookings")

@app.route("/drop_customer")
def drop_customer():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "Drop Customer"}}
    booking_collection.update_one(query, query2)
    return redirect("view_bookings")

@app.route("/extra_charges_action")
def extra_charges_action():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    print(query)
    booking = booking_collection.find_one(query)
    return render_template("extra_charges.html",booking_id=booking_id,booking=booking)


@app.route("/submit_extra_charges")
def submit_extra_charges():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    additional_charge = request.args.get("additional_charge")
    if int(additional_charge)== 0:
        query2 = {"$set": {"status": "Return Request Accepted", "additional_charge": additional_charge}}
        booking_collection.update_one(query, query2)
    else :
        reason_for_additional_charge = request.args.get("reason_for_additional_charge")
        query2 = {"$set": {"status": "Return Request Accepted", "additional_charge": additional_charge ,"reason_for_additional_charge":reason_for_additional_charge}}
        booking_collection.update_one(query, query2)
    return redirect("/view_bookings")


@app.route("/pay_remaining_amount")
def pay_remaining_amount():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    booking=booking_collection.find_one(query)
    amount = int(booking['total_amount']) * 80 / 100
    if 'additional_charge' in booking:
        extra_charges = booking['additional_charge']
    else:
        extra_charges = 0
    total_payment2 = amount + float(extra_charges)
    payment = payment_collection.find_one({"booking_id":ObjectId(booking_id)})
    return render_template("pay_remaining_amount.html",payment=payment, amount=amount, booking_id=booking_id,booking=booking,float=float,int=int,total_payment2=total_payment2,extra_charges=extra_charges)


@app.route("/payment_remaining_action")
def payment_remaining_action():
    payment_amount = request.args.get("amount")
    payment_type = request.args.get("payment_type")
    card_number = request.args.get("card_number")
    card_holder_name = request.args.get("card_holder_name")
    expiry_date = request.args.get("expiry_date")
    cvv = request.args.get("cvv")
    payment_date = datetime.now()
    booking_id = request.args.get("booking_id")
    booking = booking_collection.find_one({"_id":ObjectId(booking_id)})
    query = {"payment_amount": payment_amount, "payment_type": payment_type,
             "card_number": card_number,"booking_id":ObjectId(booking_id),
             "card_holder_name": card_holder_name, "expiry_date": expiry_date, "cvv": cvv, "payment_date": payment_date,
             "customer_id": ObjectId(booking['customer_id']), "status": 'Remaining Payment Successfully'}
    payment_collection.insert_one(query)
    query2 = {"$set": {"status": "Total Amount Paid"}}
    booking_collection.update_one({"_id":ObjectId(booking_id)},query2)
    return render_template("message_action.html", message="Payment Successfully")


@app.route("/cancel_actions")
def cancel_actions():
    booking_id = request.args.get("booking_id")
    booking_collection.delete_one({"_id":ObjectId(booking_id)},query)
    return redirect("/view_bookings")


@app.route("/view_payments")
def view_payments():
    booking_id = request.args.get("booking_id")
    query = {"booking_id": ObjectId(booking_id)}
    payments = payment_collection.find()
    return render_template("view_payments.html", payments=payments)


@app.route("/give_review_rating")
def give_review_rating():
    booking_id = request.args.get("booking_id")
    return render_template("give_review_rating.html", booking_id=booking_id)


@app.route("/give_review_action")
def give_review_action():
    booking_id = request.args.get("booking_id")
    review = request.args.get("review")
    rating = request.args.get("rating")
    customer_id = session['customer_id']
    current_time = datetime.now()
    query = {"booking_id": ObjectId(booking_id), "review": review, "rating": rating,
             "date": current_time, "customer_id": ObjectId(customer_id)}
    review_collection.insert_one(query)
    return render_template("message_action.html", message="Review Submitted successfully")



app.run(debug=True)
