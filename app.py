import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from supabase_client import supabase


def apply_custom_styles():
    st.markdown("""
    <style>
    .stApp { background-color: #f4f7fb; }
    .block-container { max-width: 900px; padding-top: 1.5rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #1f1f1f; font-weight: 700; }

    .section-card {
        background: white;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        margin-bottom: 18px;
        border: 1px solid #e9eef5;
    }

    .summary-card {
        background: white;
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        border: 1px solid #e9eef5;
        text-align: center;
        margin-bottom: 12px;
    }

    .summary-label {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 8px;
        font-weight: 600;
    }

    .summary-value {
        font-size: 28px;
        font-weight: 700;
        color: #212529;
    }

    .section-header-orange, .section-header-pink, .section-header-blue,
    .section-header-green, .section-header-purple, .section-header-dark {
        color: white;
        padding: 12px 16px;
        border-radius: 14px;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .section-header-orange { background: linear-gradient(90deg, #ff9f43, #ff7f50); }
    .section-header-pink { background: linear-gradient(90deg, #ff5c8a, #ff6f91); }
    .section-header-blue { background: linear-gradient(90deg, #5b5ce6, #6c63ff); }
    .section-header-green { background: linear-gradient(90deg, #20c997, #38d9a9); }
    .section-header-purple { background: linear-gradient(90deg, #845ef7, #9775fa); }
    .section-header-dark { background: linear-gradient(90deg, #343a40, #495057); }

    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 12px;
        font-weight: 600;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)


def get_logged_in_user():
    if "user" not in st.session_state:
        st.session_state.user = None
    return st.session_state.user


def require_auth():
    user = get_logged_in_user()
    if user is None:
        st.warning("Please log in first.")
        st.stop()
    return user


def load_table_for_user(table_name, user_id, order_column="entry_date"):
    response = (
        supabase.table(table_name)
        .select("*")
        .eq("user_id", user_id)
        .order(order_column)
        .execute()
    )
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


def filter_day(df, selected_date):
    if df.empty or "entry_date" not in df.columns:
        return pd.DataFrame()
    temp = df.copy()
    temp["entry_date"] = pd.to_datetime(temp["entry_date"]).dt.date
    return temp[temp["entry_date"] == selected_date].copy()


def display_day_table(df, columns_to_show, labels):
    if df.empty:
        st.info("No entries for this day.")
        return
    cols = [c for c in columns_to_show if c in df.columns]
    display_df = df[cols].rename(columns=labels)
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def summary_card(label, value):
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">{label}</div>
            <div class="summary-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.set_page_config(page_title="Health Tracker", layout="wide")
apply_custom_styles()

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Log Entry"

st.title("Health Tracker")

if st.session_state.user is None:
    st.caption("Sign up or log in to access your tracker")

    auth_tab1, auth_tab2 = st.tabs(["Log in", "Sign up"])

    with auth_tab1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-dark">Log in</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Log in")

            if login_submitted:
                try:
                    result = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    st.session_state.user = result.user
                    st.success("Logged in successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

    with auth_tab2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-dark">Sign up</div>', unsafe_allow_html=True)

        with st.form("signup_form"):
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_submitted = st.form_submit_button("Create account")

            if signup_submitted:
                try:
                    supabase.auth.sign_up({
                        "email": signup_email,
                        "password": signup_password
                    })
                    st.success("Account created. You can now log in.")
                except Exception as e:
                    st.error(f"Sign-up failed: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    user = require_auth()
    user_id = user.id

    st.caption(f"Logged in as {user.email}")

    top1, top2, top3, top4 = st.columns([1, 1, 1, 1])
    with top1:
        if st.button("📝 Log Entry"):
            st.session_state.page = "Log Entry"
    with top2:
        if st.button("📅 View Day"):
            st.session_state.page = "View Day"
    with top3:
        if st.button("📈 View Trends"):
            st.session_state.page = "View Trends"
    with top4:
        if st.button("Log out"):
            st.session_state.user = None
            st.rerun()

    page = st.session_state.page

    if page == "Log Entry":
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-dark">Choose what to log</div>', unsafe_allow_html=True)
        entry_type = st.selectbox("Entry type", ["Food", "Hydration", "Sleep", "Bowel Movement", "Mood"])
        st.markdown('</div>', unsafe_allow_html=True)

        if entry_type == "Food":
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header-orange">🍽️ Food</div>', unsafe_allow_html=True)
            with st.form("food_form"):
                entry_date = st.date_input("Date", value=date.today(), key="food_date")
                meal_type = st.selectbox("Meal type", ["Breakfast", "Lunch", "Dinner", "Snack"])
                food_notes = st.text_area("Food notes")
                calories = st.number_input("Calories", min_value=0, step=10)
                submitted = st.form_submit_button("Save food entry")
                if submitted:
                    supabase.table("food_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "meal_type": meal_type,
                        "food_notes": food_notes or None,
                        "calories": int(calories)
                    }).execute()
                    st.success("Food entry saved.")
            st.markdown('</div>', unsafe_allow_html=True)

        elif entry_type == "Hydration":
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header-pink">💧 Hydration</div>', unsafe_allow_html=True)
            with st.form("hydration_form"):
                entry_date = st.date_input("Date", value=date.today(), key="hydration_date")
                amount_litres = st.number_input("Amount (litres)", min_value=0.0, step=0.1)
                drink_type = st.text_input("Drink type")
                submitted = st.form_submit_button("Save hydration entry")
                if submitted:
                    supabase.table("hydration_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "amount_litres": float(amount_litres),
                        "drink_type": drink_type or None
                    }).execute()
                    st.success("Hydration entry saved.")
            st.markdown('</div>', unsafe_allow_html=True)

        elif entry_type == "Sleep":
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header-blue">😴 Sleep</div>', unsafe_allow_html=True)
            with st.form("sleep_form"):
                entry_date = st.date_input("Date", value=date.today(), key="sleep_date")
                sleep_hours = st.number_input("Sleep hours", min_value=0.0, step=0.5)
                sleep_quality = st.selectbox("Sleep quality", ["Poor", "OK", "Good", "Great"])
                submitted = st.form_submit_button("Save sleep entry")
                if submitted:
                    supabase.table("sleep_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "sleep_hours": float(sleep_hours),
                        "sleep_quality": sleep_quality
                    }).execute()
                    st.success("Sleep entry saved.")
            st.markdown('</div>', unsafe_allow_html=True)

        elif entry_type == "Bowel Movement":
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header-green">🩺 Bowel Movement</div>', unsafe_allow_html=True)
            with st.form("bowel_form"):
                entry_date = st.date_input("Date", value=date.today(), key="bowel_date")
                event_time = st.text_input("Time", placeholder="e.g. 07:30")
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("Save bowel entry")
                if submitted:
                    supabase.table("bowel_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "event_time": event_time or None,
                        "notes": notes or None
                    }).execute()
                    st.success("Bowel entry saved.")
            st.markdown('</div>', unsafe_allow_html=True)

        elif entry_type == "Mood":
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header-purple">🙂 Mood</div>', unsafe_allow_html=True)
            with st.form("mood_form"):
                entry_date = st.date_input("Date", value=date.today(), key="mood_date")
                mood_rating = st.selectbox("Mood", ["Very low", "Low", "OK", "Good", "Very good"])
                notes = st.text_area("Notes")
                submitted = st.form_submit_button("Save mood entry")
                if submitted:
                    supabase.table("mood_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "mood_rating": mood_rating,
                        "notes": notes or None
                    }).execute()
                    st.success("Mood entry saved.")
            st.markdown('</div>', unsafe_allow_html=True)

    elif page == "View Day":
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-dark">📅 View submitted data by day</div>', unsafe_allow_html=True)
        selected_day = st.date_input("Select day", value=date.today(), key="view_day")
        st.markdown('</div>', unsafe_allow_html=True)

        food_df = filter_day(load_table_for_user("food_entries", user_id), selected_day)
        hydration_df = filter_day(load_table_for_user("hydration_entries", user_id), selected_day)
        sleep_df = filter_day(load_table_for_user("sleep_entries", user_id), selected_day)
        bowel_df = filter_day(load_table_for_user("bowel_entries", user_id), selected_day)
        mood_df = filter_day(load_table_for_user("mood_entries", user_id), selected_day)

        total_calories = int(food_df["calories"].fillna(0).sum()) if not food_df.empty and "calories" in food_df.columns else 0
        total_hydration = round(float(hydration_df["amount_litres"].fillna(0).sum()), 1) if not hydration_df.empty and "amount_litres" in hydration_df.columns else 0
        total_sleep = round(float(sleep_df["sleep_hours"].fillna(0).sum()), 1) if not sleep_df.empty and "sleep_hours" in sleep_df.columns else 0
        total_bowel = len(bowel_df)
        total_mood = len(mood_df)

        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            summary_card("Calories", total_calories)
        with s2:
            summary_card("Hydration (L)", total_hydration)
        with s3:
            summary_card("Sleep (hrs)", total_sleep)
        with s4:
            summary_card("Bowel entries", total_bowel)
        with s5:
            summary_card("Mood entries", total_mood)

        st.markdown("### 🍽️ Food")
        display_day_table(food_df, ["entry_date", "meal_type", "food_notes", "calories"], {
            "entry_date": "Date", "meal_type": "Meal", "food_notes": "Food", "calories": "Calories"
        })

        st.markdown("### 💧 Hydration")
        display_day_table(hydration_df, ["entry_date", "amount_litres", "drink_type"], {
            "entry_date": "Date", "amount_litres": "Litres", "drink_type": "Drink"
        })

        st.markdown("### 😴 Sleep")
        display_day_table(sleep_df, ["entry_date", "sleep_hours", "sleep_quality"], {
            "entry_date": "Date", "sleep_hours": "Hours", "sleep_quality": "Quality"
        })

        st.markdown("### 🩺 Bowel Movements")
        display_day_table(bowel_df, ["entry_date", "event_time", "notes"], {
            "entry_date": "Date", "event_time": "Time", "notes": "Notes"
        })

        st.markdown("### 🙂 Mood")
        display_day_table(mood_df, ["entry_date", "mood_rating", "notes"], {
            "entry_date": "Date", "mood_rating": "Mood", "notes": "Notes"
        })

    elif page == "View Trends":
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-dark">📈 Longer-term trends</div>', unsafe_allow_html=True)

        trend_range = st.selectbox("Time range", ["Last 7 days", "Last 14 days", "Last 30 days", "Custom"])
        if trend_range == "Last 7 days":
            start_date = date.today() - timedelta(days=6)
            end_date = date.today()
        elif trend_range == "Last 14 days":
            start_date = date.today() - timedelta(days=13)
            end_date = date.today()
        elif trend_range == "Last 30 days":
            start_date = date.today() - timedelta(days=29)
            end_date = date.today()
        else:
            a, b = st.columns(2)
            with a:
                start_date = st.date_input("Start date", value=date.today() - timedelta(days=6), key="trend_start")
            with b:
                end_date = st.date_input("End date", value=date.today(), key="trend_end")

        st.markdown('</div>', unsafe_allow_html=True)

        def range_filter(df):
            if df.empty or "entry_date" not in df.columns:
                return pd.DataFrame()
            temp = df.copy()
            temp["entry_date"] = pd.to_datetime(temp["entry_date"])
            return temp[(temp["entry_date"].dt.date >= start_date) & (temp["entry_date"].dt.date <= end_date)]

        food_df = range_filter(load_table_for_user("food_entries", user_id))
        hydration_df = range_filter(load_table_for_user("hydration_entries", user_id))
        sleep_df = range_filter(load_table_for_user("sleep_entries", user_id))
        bowel_df = range_filter(load_table_for_user("bowel_entries", user_id))
        mood_df = range_filter(load_table_for_user("mood_entries", user_id))

        st.markdown("### Food — calories by day")
        if not food_df.empty and "calories" in food_df.columns:
            daily = prepare_daily_series(food_df, "entry_date", "calories")
            daily = daily[(daily["entry_date"].dt.date >= start_date) & (daily["entry_date"].dt.date <= end_date)]
            fig = px.line(daily, x="entry_date", y="calories", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No food data in this range.")

        st.markdown("### Hydration — litres by day")
        if not hydration_df.empty and "amount_litres" in hydration_df.columns:
            daily = prepare_daily_series(hydration_df, "entry_date", "amount_litres")
            daily = daily[(daily["entry_date"].dt.date >= start_date) & (daily["entry_date"].dt.date <= end_date)]
            fig = px.line(daily, x="entry_date", y="amount_litres", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hydration data in this range.")

        st.markdown("### Sleep — hours by day")
        if not sleep_df.empty and "sleep_hours" in sleep_df.columns:
            daily = prepare_daily_series(sleep_df, "entry_date", "sleep_hours")
            daily = daily[(daily["entry_date"].dt.date >= start_date) & (daily["entry_date"].dt.date <= end_date)]
            fig = px.line(daily, x="entry_date", y="sleep_hours", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sleep data in this range.")