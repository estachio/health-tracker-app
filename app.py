import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from supabase_client import supabase


def apply_custom_styles():
    st.markdown("""
    <style>
    .stApp {
        background-color: #f4f7fb;
    }

    h1, h2, h3 {
        color: #1f1f1f;
        font-weight: 700;
    }

    .section-card {
        background: white;
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        margin-bottom: 24px;
        border: 1px solid #e9eef5;
    }

    .section-header-orange {
        background: linear-gradient(90deg, #ff9f43, #ff7f50);
        color: white;
        padding: 14px 18px;
        border-radius: 14px;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 16px;
    }

    .section-header-pink {
        background: linear-gradient(90deg, #ff5c8a, #ff6f91);
        color: white;
        padding: 14px 18px;
        border-radius: 14px;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 16px;
    }

    .section-header-blue {
        background: linear-gradient(90deg, #5b5ce6, #6c63ff);
        color: white;
        padding: 14px 18px;
        border-radius: 14px;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 16px;
    }

    .section-header-green {
        background: linear-gradient(90deg, #20c997, #38d9a9);
        color: white;
        padding: 14px 18px;
        border-radius: 14px;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 16px;
    }

    .section-header-purple {
        background: linear-gradient(90deg, #845ef7, #9775fa);
        color: white;
        padding: 14px 18px;
        border-radius: 14px;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 16px;
    }

    .small-help {
        color: #5f6b7a;
        font-size: 14px;
        margin-bottom: 12px;
    }

    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 12px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }

    [data-baseweb="tab-list"] {
        gap: 8px;
    }

    [data-baseweb="tab"] {
        background-color: white;
        border-radius: 12px 12px 0 0;
        padding: 10px 16px;
    }
    </style>
    """, unsafe_allow_html=True)


def load_table(table_name, order_column="entry_date"):
    response = supabase.table(table_name).select("*").order(order_column).execute()
    return pd.DataFrame(response.data if response.data else [])


def prepare_daily_series(df, date_col, value_col):
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()

    working_df = df.copy()
    working_df[date_col] = pd.to_datetime(working_df[date_col])

    daily = (
        working_df.groupby(date_col, as_index=False)[value_col]
        .sum()
        .sort_values(date_col)
    )

    full_date_range = pd.date_range(
        start=daily[date_col].min(),
        end=daily[date_col].max(),
        freq="D"
    )

    full_df = pd.DataFrame({date_col: full_date_range})
    daily = full_df.merge(daily, on=date_col, how="left")
    daily[value_col] = daily[value_col].fillna(0)

    return daily


st.set_page_config(page_title="Health Tracker", layout="wide")
apply_custom_styles()

st.title("Health Tracker")
st.caption("A simple daily tracker for food, hydration, sleep, bowel movements and mood")

main_tab1, main_tab2 = st.tabs(["Data Entry", "Visualisations"])

with main_tab1:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Food",
        "Hydration",
        "Sleep",
        "Bowel Movements",
        "Mood"
    ])

    with tab1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-orange">🍽️ Food</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-help">Log meals and calories for the day.</div>', unsafe_allow_html=True)

        with st.form("food_form"):
            entry_date = st.date_input("Date", value=date.today(), key="food_date")
            meal_type = st.selectbox("Meal type", ["Breakfast", "Lunch", "Dinner", "Snack"], key="meal_type")
            food_notes = st.text_area("Food notes", key="food_notes")
            calories = st.number_input("Calories", min_value=0, step=10, key="calories")
            submitted = st.form_submit_button("Save food entry")

            if submitted:
                data = {
                    "entry_date": entry_date.isoformat(),
                    "meal_type": meal_type,
                    "food_notes": food_notes or None,
                    "calories": int(calories)
                }
                supabase.table("food_entries").insert(data).execute()
                st.success("Food entry saved.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-pink">💧 Hydration</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-help">Track drinks and total fluid intake.</div>', unsafe_allow_html=True)

        with st.form("hydration_form"):
            entry_date = st.date_input("Date", value=date.today(), key="hydration_date")
            amount_litres = st.number_input("Amount (litres)", min_value=0.0, step=0.1, key="amount_litres")
            drink_type = st.text_input("Drink type", key="drink_type")
            submitted = st.form_submit_button("Save hydration entry")

            if submitted:
                data = {
                    "entry_date": entry_date.isoformat(),
                    "amount_litres": float(amount_litres),
                    "drink_type": drink_type or None
                }
                supabase.table("hydration_entries").insert(data).execute()
                st.success("Hydration entry saved.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-blue">😴 Sleep</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-help">Log how long you slept and how good it felt.</div>', unsafe_allow_html=True)

        with st.form("sleep_form"):
            entry_date = st.date_input("Date", value=date.today(), key="sleep_date")
            sleep_hours = st.number_input("Sleep hours", min_value=0.0, step=0.5, key="sleep_hours")
            sleep_quality = st.selectbox("Sleep quality", ["Poor", "OK", "Good", "Great"], key="sleep_quality")
            submitted = st.form_submit_button("Save sleep entry")

            if submitted:
                data = {
                    "entry_date": entry_date.isoformat(),
                    "sleep_hours": float(sleep_hours),
                    "sleep_quality": sleep_quality
                }
                supabase.table("sleep_entries").insert(data).execute()
                st.success("Sleep entry saved.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-green">🩺 Bowel Movements</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-help">Record bowel events for comparison over time.</div>', unsafe_allow_html=True)

        with st.form("bowel_form"):
            entry_date = st.date_input("Date", value=date.today(), key="bowel_date")
            event_time = st.text_input("Time", placeholder="e.g. 07:30", key="event_time")
            notes = st.text_area("Notes", key="bowel_notes")
            submitted = st.form_submit_button("Save bowel entry")

            if submitted:
                data = {
                    "entry_date": entry_date.isoformat(),
                    "event_time": event_time or None,
                    "notes": notes or None
                }
                supabase.table("bowel_entries").insert(data).execute()
                st.success("Bowel entry saved.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-purple">🙂 Mood</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-help">Track your mood and add notes if helpful.</div>', unsafe_allow_html=True)

        with st.form("mood_form"):
            entry_date = st.date_input("Date", value=date.today(), key="mood_date")
            mood_rating = st.selectbox("Mood", ["Very low", "Low", "OK", "Good", "Very good"], key="mood_rating")
            notes = st.text_area("Notes", key="mood_notes")
            submitted = st.form_submit_button("Save mood entry")

            if submitted:
                data = {
                    "entry_date": entry_date.isoformat(),
                    "mood_rating": mood_rating,
                    "notes": notes or None
                }
                supabase.table("mood_entries").insert(data).execute()
                st.success("Mood entry saved.")
        st.markdown('</div>', unsafe_allow_html=True)

with main_tab2:
    st.subheader("Visualisations")

    food_df = load_table("food_entries")
    hydration_df = load_table("hydration_entries")
    sleep_df = load_table("sleep_entries")
    bowel_df = load_table("bowel_entries")
    mood_df = load_table("mood_entries")

    st.markdown("### Food — total calories per day")
    if not food_df.empty and "calories" in food_df.columns:
        food_daily = prepare_daily_series(food_df, "entry_date", "calories")
        food_chart = px.line(
            food_daily,
            x="entry_date",
            y="calories",
            title="Daily calorie intake",
            markers=True
        )
        food_chart.update_traces(line=dict(color="#ff8c42", width=3))
        food_chart.update_xaxes(dtick="D", tickformat="%d %b")
        st.plotly_chart(food_chart, use_container_width=True)
    else:
        st.info("No food data available.")

    st.markdown("### Hydration — total litres per day")
    if not hydration_df.empty and "amount_litres" in hydration_df.columns:
        hydration_daily = prepare_daily_series(hydration_df, "entry_date", "amount_litres")
        hydration_chart = px.line(
            hydration_daily,
            x="entry_date",
            y="amount_litres",
            title="Daily hydration total",
            markers=True
        )
        hydration_chart.update_traces(line=dict(color="#ff5c8a", width=3))
        hydration_chart.update_xaxes(dtick="D", tickformat="%d %b")
        st.plotly_chart(hydration_chart, use_container_width=True)
    else:
        st.info("No hydration data available.")

    st.markdown("### Sleep — total hours per day")
    if not sleep_df.empty and "sleep_hours" in sleep_df.columns:
        sleep_daily = prepare_daily_series(sleep_df, "entry_date", "sleep_hours")
        sleep_chart = px.line(
            sleep_daily,
            x="entry_date",
            y="sleep_hours",
            title="Daily sleep total",
            markers=True
        )
        sleep_chart.update_traces(line=dict(color="#5b5ce6", width=3))
        sleep_chart.update_xaxes(dtick="D", tickformat="%d %b")
        st.plotly_chart(sleep_chart, use_container_width=True)
    else:
        st.info("No sleep data available.")

    st.markdown("### Bowel movements — comparison table")
    if not bowel_df.empty:
        st.dataframe(bowel_df, use_container_width=True)
    else:
        st.info("No bowel movement data available.")

    st.markdown("### Mood — comparison table")
    if not mood_df.empty:
        st.dataframe(mood_df, use_container_width=True)
    else:
        st.info("No mood data available.")