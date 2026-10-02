"""Price forecasting using scikit-learn linear regression on monthly price data."""

from datetime import timedelta

import numpy as np
import pandas as pd
from django.utils import timezone
from sklearn.linear_model import LinearRegression

from .models import PriceRecord


def _build_features(dates, base_date=None):
    """Create time-based features using a common training base date."""

    dates = pd.Series(pd.to_datetime(dates))

    if base_date is None:
        base = dates.min()
    else:
        base = pd.Timestamp(base_date)

    day_index = (
        dates - base
    ).dt.days.values.reshape(-1, 1)

    day_of_year = dates.dt.dayofyear.values

    seasonal_sin = np.sin(
        2 * np.pi * day_of_year / 365
    ).reshape(-1, 1)

    seasonal_cos = np.cos(
        2 * np.pi * day_of_year / 365
    ).reshape(-1, 1)

    return np.hstack([
        day_index,
        seasonal_sin,
        seasonal_cos
    ])


def forecast_prices(crop, district, months_ahead=3):
    """
    Forecast prices for a crop and district.

    Historical display:
        January 2024 → September 2026

    Forecast display:
        Next 3 months after the latest historical month.

    Price records are aggregated into monthly average prices
    so the chart remains clean and readable.
    """

    records = PriceRecord.objects.filter(
        crop=crop,
        district=district
    ).order_by("date")

    if records.count() < 6:
        return {
            "error": "Insufficient price data for forecasting.",
            "historical": [],
            "forecast": [],
            "is_synthetic": False,
        }

    # Load price records into a DataFrame
    df = pd.DataFrame(
        list(
            records.values(
                "date",
                "price"
            )
        )
    )

    df["date"] = pd.to_datetime(df["date"])
    df["price"] = df["price"].astype(float)

    # ---------------------------------------------------------
    # Convert daily/multiple records into monthly averages
    # ---------------------------------------------------------

    df["month"] = df["date"].dt.to_period("M")

    monthly_df = (
        df.groupby("month", as_index=False)["price"]
        .mean()
    )

    monthly_df["date"] = (
        monthly_df["month"]
        .dt.to_timestamp()
    )

    monthly_df = monthly_df.sort_values("date").reset_index(
        drop=True
    )

    if len(monthly_df) < 6:
        return {
            "error": "Insufficient monthly price data for forecasting.",
            "historical": [],
            "forecast": [],
            "is_synthetic": False,
        }

    # ---------------------------------------------------------
    # Prepare ML training data
    # ---------------------------------------------------------

    training_base = monthly_df["date"].min()

    X = _build_features(
        monthly_df["date"],
        base_date=training_base
    )

    y = monthly_df["price"].values

    model = LinearRegression()

    model.fit(X, y)

    # ---------------------------------------------------------
    # Determine forecast months
    # ---------------------------------------------------------

    last_month = monthly_df["date"].max().to_period("M")

    first_forecast_month = (
        last_month + 1
    ).to_timestamp()

    forecast_dates = pd.date_range(
        start=first_forecast_month,
        periods=months_ahead,
        freq="MS"
    )

    # IMPORTANT:
    # Future features use the SAME training base date.
    X_future = _build_features(
        forecast_dates,
        base_date=training_base
    )

    predictions = model.predict(X_future)

    # ---------------------------------------------------------
    # Calculate forecast range
    # ---------------------------------------------------------

    std_dev = monthly_df["price"].std()

    if pd.isna(std_dev):
        std_dev = 0

    forecast = []

    for dt, pred in zip(
        forecast_dates,
        predictions
    ):

        predicted_price = float(pred)

        low_price = max(
            0,
            predicted_price - float(std_dev)
        )

        high_price = (
            predicted_price + float(std_dev)
        )

        forecast.append({
            "date": dt.date().isoformat(),
            "price": round(predicted_price, 2),
            "low": round(low_price, 2),
            "high": round(high_price, 2),
        })

    # ---------------------------------------------------------
    # Historical monthly data
    # ---------------------------------------------------------

    historical = []

    for _, row in monthly_df.iterrows():

        historical.append({
            "date": row["date"].date().isoformat(),
            "price": round(
                float(row["price"]),
                2
            ),
        })

    # ---------------------------------------------------------
    # Check whether data is synthetic
    # ---------------------------------------------------------

    is_synthetic = records.filter(
        is_synthetic=True
    ).exists()

    # ---------------------------------------------------------
    # Recent average
    # ---------------------------------------------------------

    current_avg = monthly_df["price"].tail(3).mean()

    return {
        "historical": historical,
        "forecast": forecast,
        "is_synthetic": is_synthetic,
        "crop": crop.name,
        "district": district,
        "current_avg": round(
            float(current_avg),
            2
        ),
    }