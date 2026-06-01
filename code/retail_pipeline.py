import pandas as pd
import numpy as np
import hashlib
import logging
from pathlib import Path

logging.basicConfig( level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s" )
logger = logging.getLogger(__name__)

RETAIL_FILE_1 = "retail_data1.xlsx"
RETAIL_FILE_2 = "retail_data2.xlsx"
PRODUCT_FILE = "product_details.xlsx"

OUTPUT_FOLDER = Path("Output")
OUTPUT_FOLDER.mkdir(exist_ok=True)
#----------------------------------------------------#
def hash_email(email):
    if pd.isna(email):
        return np.nan

    return hashlib.sha256(str(email).encode() ).hexdigest()
#----------------------------------------------------#
def mask_phone(phone):
    if pd.isna(phone):
        return np.nan
    phone = str(phone)
    if len(phone) < 4:
        return "XXXX"
    return phone[:2] + "******" + phone[-2:]
#----------------------------------------------------#

retail_1 = pd.read_excel(RETAIL_FILE_1)
retail_2 = pd.read_excel(RETAIL_FILE_2)
product_dim = pd.read_excel(PRODUCT_FILE)
retail_df = pd.concat([retail_1, retail_2],ignore_index=True)

missing_report = retail_df.isnull().sum()
missing_report.to_csv(OUTPUT_FOLDER / "missing_value_report.csv")

retail_df["product_name"] = (
    retail_df["product_name"].astype(str).str.strip().str.title()
)

product_dim["product_name"] = (
    product_dim["product_name"].astype(str).str.strip().str.title()
)

retail_df["transaction_date"] = pd.to_datetime(retail_df["transaction_date"],errors="coerce")

invalid_quantity_count = len(retail_df[retail_df["quantity"] <= 0])

retail_df = retail_df[retail_df["quantity"] > 0]

product_dim = product_dim.rename(
    columns={"category": "master_category","price": "master_price"}
)

retail_df = retail_df.merge(
    product_dim,on=["product_id", "product_name"],how="left"
)

retail_df["price"] = retail_df["price"].fillna(
    retail_df["master_price"]
)

retail_df["category"] = retail_df["master_category"]

retail_df["email_hash"] = (
    retail_df["email"].apply(hash_email)
)

retail_df["phone"] = (
    retail_df["phone"].apply(mask_phone)
)

retail_df.drop(
    columns=["email"],inplace=True
)

retail_df["revenue"] = (
    retail_df["price"] * retail_df["quantity"] * (1 - retail_df["discount"])
)

retail_df["year"] = (
    retail_df["transaction_date"].dt.year
)

retail_df["month"] = (
    retail_df["transaction_date"].dt.month_name()
)


retail_df.to_csv(
    OUTPUT_FOLDER / "retail_curated_dataset.csv",index=False
)

successful_sales = retail_df[ retail_df["payment_status"].str.lower() == "successful" ].copy()
total_revenue = successful_sales["revenue"].sum()
total_transactions = (successful_sales["transaction_id"].nunique() )
total_customers = (successful_sales["customer_id"].nunique())
successful_count = len(successful_sales)

failed_count = len(retail_df[retail_df["payment_status"].str.lower()== "failed"])

average_order_value = (
    total_revenue / total_transactions
    if total_transactions > 0
    else 0
)

kpi_summary = pd.DataFrame({
    "Metric": [
        "Total Revenue",
        "Total Transactions",
        "Total Customers",
        "Successful Transactions",
        "Failed Transactions",
        "Average Order Value"
    ],
    "Value": [
        total_revenue,
        total_transactions,
        total_customers,
        successful_count,
        failed_count,
        average_order_value
    ]
})

kpi_summary.to_csv(
    OUTPUT_FOLDER / "kpi_summary.csv",
    index=False
)

revenue_by_category = (
    successful_sales.groupby("category")["revenue"].sum().reset_index().sort_values(by="revenue",ascending=False)
)

revenue_by_category.to_csv(
    OUTPUT_FOLDER / "revenue_by_category.csv",
    index=False
)

revenue_by_city = (
    successful_sales.groupby("city")["revenue"].sum().reset_index().sort_values(by="revenue",ascending=False)
)

revenue_by_city.to_csv(
    OUTPUT_FOLDER / "revenue_by_city.csv",
    index=False
)

best_selling_products = (
    successful_sales.groupby("product_name")["quantity"].sum().reset_index().sort_values(by="quantity",ascending=False)
)

best_selling_products.to_csv(
    OUTPUT_FOLDER / "top_products.csv",
    index=False
)

payment_analysis = (
    successful_sales.groupby("payment_method")["revenue"].sum().reset_index()
)

payment_analysis.to_csv(
    OUTPUT_FOLDER / "payment_analysis.csv",
    index=False
)

monthly_revenue = (
    successful_sales.groupby(["year", "month"])["revenue"].sum().reset_index()
)

monthly_revenue.to_csv(
    OUTPUT_FOLDER / "monthly_revenue.csv",
    index=False
)
print("\nSuccessfully")
print("Output files saved")