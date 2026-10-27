import streamlit as st
import hashlib
import json
import os
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
import pandas as pd
import plotly.express as px

DATA_FILE = "blockchain_data.json"

from blockchain_core import Block, Blockchain


def load_chain():
    if not os.path.exists(DATA_FILE):
        return Blockchain()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            records = json.load(file)
        return Blockchain.from_list(records)
    except (json.JSONDecodeError, OSError, KeyError, TypeError) as exc:
        st.error(f"Could not load {DATA_FILE}: {exc}")
        return Blockchain()


def save_chain(chain):
    temp_file = DATA_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(chain.to_list(), file, indent=2, ensure_ascii=False)
    os.replace(temp_file, DATA_FILE)


def format_money(value):
    return f"₹{value:,.2f}"


st.set_page_config(page_title="Blockchain Expense Tracker", page_icon="🔗", layout="wide")
st.title("🔗 Blockchain Expense Tracker")
st.caption("A learning project demonstrating linked transaction blocks and SHA-256 integrity checks.")

if "chain" not in st.session_state:
    st.session_state.chain = load_chain()

chain = st.session_state.chain
valid, validation_message = chain.is_valid()

with st.sidebar:
    st.header("Add a transaction")
    tx_type = st.radio("Transaction type", ["Expense", "Income"], horizontal=True)
    amount_text = st.text_input("Amount (INR)", placeholder="e.g. 250.00")
    category_options = (
        ["Food", "Transport", "Education", "Shopping", "Bills", "Health", "Entertainment", "Other"]
        if tx_type == "Expense"
        else ["Salary", "Allowance", "Freelance", "Gift", "Refund", "Other"]
    )
    category = st.selectbox("Category", category_options)
    description = st.text_input("Description", placeholder="e.g. Lunch")
    tx_date = st.date_input(
        "Transaction date",
        value=date.today(),
        help="You can select any date for each income or expense. Different transactions can have different dates."
    )
    add_clicked = st.button("Add to blockchain", type="primary", use_container_width=True)

    if add_clicked:
        try:
            amount = Decimal(amount_text.strip())
            if not amount.is_finite() or amount <= 0:
                st.error("Enter an amount greater than zero.")
            elif len(description.strip()) == 0:
                st.error("Enter a short description.")
            else:
                transaction = {
                    "type": tx_type.upper(),
                    "amount": str(amount.quantize(Decimal("0.01"))),
                    "category": category,
                    "description": description.strip(),
                    "transaction_date": tx_date.isoformat(),
                }
                chain.add_transaction(transaction)
                save_chain(chain)
                st.session_state.chain = chain
                st.success("Transaction added as a new block.")
                st.rerun()
        except InvalidOperation:
            st.error("Enter a valid numeric amount, for example 125.50.")

    st.divider()
    st.subheader("Blockchain tools")
    if st.button("Verify blockchain", use_container_width=True):
        st.session_state.last_verify = chain.is_valid()
    if st.button("Export blockchain JSON", use_container_width=True):
        st.download_button(
            "Download JSON file",
            data=json.dumps(chain.to_list(), indent=2, ensure_ascii=False),
            file_name="blockchain_expenses.json",
            mime="application/json",
            use_container_width=True,
        )
    if st.button("Create sample data", use_container_width=True):
        if len(chain.chain) == 1:
            today = date.today()
            examples = [
                {"type": "INCOME", "amount": "15000.00", "category": "Allowance",
                 "description": "Monthly allowance", "transaction_date": today.isoformat()},
                {"type": "EXPENSE", "amount": "180.00", "category": "Food",
                 "description": "Lunch", "transaction_date": today.isoformat()},
                {"type": "EXPENSE", "amount": "75.00", "category": "Transport",
                 "description": "Bus fare", "transaction_date": today.isoformat()},
                {"type": "EXPENSE", "amount": "450.00", "category": "Shopping",
                 "description": "Groceries", "transaction_date": (today - timedelta(days=2)).isoformat()},
                {"type": "INCOME", "amount": "2000.00", "category": "Freelance",
                 "description": "Side project payment", "transaction_date": (today - timedelta(days=1)).isoformat()},
            ]
            for example in examples:
                chain.add_transaction(example)
            save_chain(chain)
            st.session_state.chain = chain
            st.rerun()
        else:
            st.info("Sample data is added only to a new chain.")

    st.divider()
    st.subheader("Danger zone")
    confirm_reset = st.checkbox("I understand this will delete all transactions", key="confirm_reset")
    if st.button("Reset blockchain", type="secondary", use_container_width=True, disabled=not confirm_reset):
        new_chain = Blockchain()
        save_chain(new_chain)
        st.session_state.chain = new_chain
        st.success("Blockchain has been reset to the genesis block.")
        st.rerun()

st.subheader("Blockchain integrity")
valid, validation_message = chain.is_valid()
if valid:
    st.success(f"✅ {validation_message}")
else:
    st.error(f"⚠️ {validation_message}")
st.caption("This is a local educational blockchain, not a public blockchain or a security audit system.")

transactions = [
    {"Block": b.index, **b.transaction, "Timestamp": b.timestamp, "Hash": b.hash,
     "Previous hash": b.previous_hash}
    for b in chain.chain if b.index > 0
]
df = pd.DataFrame(transactions)

if df.empty:
    st.info("No transactions yet. Add a transaction in the sidebar or create sample data.")
    st.metric("Blocks in chain", len(chain.chain))
else:
    df["amount_numeric"] = pd.to_numeric(df["amount"], errors="coerce")

    income_total = df.loc[df["type"] == "INCOME", "amount_numeric"].sum()
    expense_total = df.loc[df["type"] == "EXPENSE", "amount_numeric"].sum()
    balance = income_total - expense_total

    st.subheader("Overall summary (All dates)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total income", format_money(income_total))
    c2.metric("Total expenses", format_money(expense_total))
    c3.metric("Net balance", format_money(balance))
    c4.metric("Blocks in chain", len(chain.chain))

    st.subheader("Day-wise summary")
    available_dates = sorted(df["transaction_date"].dropna().unique().tolist())

    if available_dates:
        day_cols = st.columns(min(len(available_dates), 4))
        for idx, day in enumerate(available_dates):
            day_df = df[df["transaction_date"] == day]
            day_income = day_df.loc[day_df["type"] == "INCOME", "amount_numeric"].sum()
            day_expense = day_df.loc[day_df["type"] == "EXPENSE", "amount_numeric"].sum()
            day_net = day_income - day_expense
            with day_cols[idx % len(day_cols)]:
                st.markdown(f"### {day}")
                st.metric("Income", format_money(day_income))
                st.metric("Expense", format_money(day_expense))
                st.metric("Net", format_money(day_net))
                st.caption(f"{len(day_df)} transaction(s)")

    st.subheader("Detailed visualization")
    date_options = ["All dates (Total)"] + available_dates
    selected_view = st.selectbox(
        "Choose date for charts & table",
        options=date_options,
        help="Select a specific date to see only that day's charts, or All dates for combined view."
    )

    if selected_view == "All dates (Total)":
        filtered_df = df.copy()
        view_label = "All dates"
    else:
        filtered_df = df[df["transaction_date"] == selected_view].copy()
        view_label = selected_view

    f_income = filtered_df.loc[filtered_df["type"] == "INCOME", "amount_numeric"].sum()
    f_expense = filtered_df.loc[filtered_df["type"] == "EXPENSE", "amount_numeric"].sum()

    st.markdown(f"**Charts for: `{view_label}`**")

    left, right = st.columns(2)
    with left:
        expense_df = filtered_df[filtered_df["type"] == "EXPENSE"]
        if not expense_df.empty:
            category_summary = expense_df.groupby("category", as_index=False)["amount_numeric"].sum()
            fig = px.pie(
                category_summary,
                names="category",
                values="amount_numeric",
                title=f"Expenses by category — {view_label}",
                hole=0.35,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses for the selected date.")
    with right:
        totals = pd.DataFrame({
            "Type": ["Income", "Expense"],
            "Amount": [f_income, f_expense],
        })
        fig = px.bar(
            totals,
            x="Type",
            y="Amount",
            title=f"Income vs expenses — {view_label}",
            text_auto=".2f",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Daily Income vs Expense comparison")
    daily = (
        df.groupby(["transaction_date", "type"])["amount_numeric"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    if "INCOME" not in daily.columns:
        daily["INCOME"] = 0.0
    if "EXPENSE" not in daily.columns:
        daily["EXPENSE"] = 0.0
    daily = daily.rename(columns={"transaction_date": "Date", "INCOME": "Income", "EXPENSE": "Expense"})
    daily["Net"] = daily["Income"] - daily["Expense"]

    daily_melt = daily.melt(id_vars="Date", value_vars=["Income", "Expense"], var_name="Type", value_name="Amount")
    fig_daily = px.bar(
        daily_melt,
        x="Date",
        y="Amount",
        color="Type",
        barmode="group",
        title="Daily Income vs Expense",
        text_auto=".2f",
    )
    st.plotly_chart(fig_daily, use_container_width=True)

    st.dataframe(daily.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)

    st.subheader(f"Transaction history — {view_label}")
    display_df = filtered_df[["Block", "transaction_date", "type", "category", "description", "amount"]].copy()
    display_df.columns = ["Block", "Date", "Type", "Category", "Description", "Amount (INR)"]
    st.dataframe(display_df.sort_values("Block", ascending=False), use_container_width=True, hide_index=True)

    with st.expander("Inspect blockchain blocks"):
        for block in reversed(chain.chain):
            st.markdown(f"**Block {block.index}** · {block.timestamp}")
            st.json(block.to_dict())

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered transaction history (CSV)",
        data=csv,
        file_name="expense_transactions.csv",
        mime="text/csv",
    )

st.divider()
st.markdown("---")


st.markdown(
    """
    <div style="
        text-align: center;
        padding: 12px;
        background-color: #16213e;
        border-radius: 10px;
        color: white;
    ">
        <p style="margin: 0; color: #feca57;">Built by</p>
        <p style="margin: 6px 0 0 0; color: #ff6b81; font-weight: bold;">
            Sarthak Jain  • Yogesh Singh • Atharv Sharma
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
 