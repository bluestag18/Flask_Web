from flask import Flask, request, render_template, redirect, url_for, flash
import psycopg2

app = Flask(__name__)
app.secret_key = "your_secret_key"  

DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "athavsaveu"

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM flask.users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if user:
            user_type = user[3]  
            if user_type == "buyer":
                return redirect(url_for("buyer_dashboard", username=username))
            elif user_type == "seller":
                return redirect(url_for("seller_interface", username=username))
        else:
            flash("WHAT BRO... IT IS VERY WRONG BRO")
            return redirect(url_for("login"))
    
    return render_template("login.html")

@app.route("/buyer_dashboard/<username>", methods=["GET", "POST"])
def buyer_dashboard(username):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        # Get form data
        description = request.form.get("description")
        budget = request.form.get("budget")

        # Insert into the database
        cur.execute(
            "INSERT INTO flask.deals (description, budget) VALUES (%s, %s)",
            (description, budget)
        )
        conn.commit()

    # Fetch all active deals
    cur.execute("SELECT * FROM flask.deals")
    active_deals = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("buyer_dashboard.html", username=username, active_deals=active_deals)

@app.route("/remove_deal", methods=["POST"])
def remove_deal():
    # Get the deal_id from the POST request
    deal_id = request.form.get("deal_id")

    if not deal_id:
        return "Invalid Request: No deal ID provided", 400  # Handle missing deal_id

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Delete the deal from the database
        cur.execute("DELETE FROM flask.deals WHERE id = %s", (deal_id,))
        conn.commit()

        # Debugging: Confirm the deal was deleted
        print(f"Deleted deal with ID: {deal_id}")

    except Exception as e:
        print(f"Error deleting deal: {e}")
        conn.rollback()  # Roll back if there's an error
        return "Failed to delete deal", 500

    finally:
        cur.close()
        conn.close()

    # Redirect back to the buyer dashboard (username must be passed via form or hardcoded)
    username = request.form.get("username", "default_user")  # Replace "default_user" if needed
    return redirect(url_for("buyer_dashboard", username=username))

@app.route('/seller_interface')
def seller_interface():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM flask.deals")
    deals = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('seller_interface.html', deals=deals)

@app.route('/place_or_edit_bid', methods=['POST'])
def place_or_edit_bid():
    deal_id = request.form['deal_id']
    bid_amount = request.form['bid_amount']

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT bid FROM flask.deals WHERE id = %s", (deal_id,))
        existing_bid = cur.fetchone()
        if existing_bid and existing_bid[0]:
            cur.execute("UPDATE flask.deals SET bid = %s WHERE id = %s", (bid_amount, deal_id))
        else:
            cur.execute("UPDATE flask.deals SET bid = %s WHERE id = %s", (bid_amount, deal_id))
        conn.commit()
    except Exception as e:
        print("Database error:", e)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('seller_interface'))



if __name__ == "__main__":
    app.run(debug=True)
