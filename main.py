from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "supersecretkey"
db = SQLAlchemy(app)

# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)

# Budget Model
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False, default=0)

# Initialize Database
with app.app_context():
    db.create_all()

# Home Page
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            if "set_budget" in request.form:  # Set Budget
                budget_amount = float(request.form.get("budget"))
                budget_entry = Budget.query.first()
                if budget_entry:
                    budget_entry.amount = budget_amount
                else:
                    budget_entry = Budget(amount=budget_amount)
                    db.session.add(budget_entry)
                db.session.commit()
                flash("Budget set successfully!", "success")
            else:  # Add Expense
                amount = request.form.get("amount")
                category = request.form.get("category")

                if not amount or not category:
                    flash("All fields are required!", "warning")
                    return redirect(url_for("index"))

                amount = float(amount)
                if amount <= 0:
                    flash("Amount must be greater than zero!", "danger")
                    return redirect(url_for("index"))

                new_expense = Expense(amount=amount, category=category)
                db.session.add(new_expense)
                db.session.commit()
                flash("Expense added successfully!", "success")

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")

        return redirect(url_for("index"))

    expenses = Expense.query.order_by(Expense.date.desc()).all()
    total_expenses = sum(exp.amount for exp in expenses)
    budget_entry = Budget.query.first()
    budget = budget_entry.amount if budget_entry else 0

    # Budget Warning
    budget_warning = None
    if budget > 0 and total_expenses >= 0.8 * budget:
        budget_warning = f"⚠️ Warning: You have used {int((total_expenses / budget) * 100)}% of your budget!"

    # Category-wise Breakdown
    category_data = {}
    for exp in expenses:
        category_data[exp.category] = category_data.get(exp.category, 0) + exp.amount

    return render_template("index.html", expenses=expenses, total=total_expenses, 
                           budget=budget, budget_warning=budget_warning, category_data=category_data)

# Delete Expense
@app.route("/delete/<int:id>")
def delete_expense(id):
    expense_to_delete = Expense.query.get_or_404(id)
    try:
        db.session.delete(expense_to_delete)
        db.session.commit()
        flash("Expense deleted successfully!", "success")
    except:
        flash("Error deleting expense!", "danger")

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)


