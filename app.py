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


def policy_note():
    st.caption("Editing needs UPDATE policies. Deleting needs DELETE policies.")


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

if "page" not in st.session_state:
    st.session_state.page = "Log Entry"

st.title("Health Tracker")
st.caption("Mobile-friendly daily tracking for food, hydration, sleep, bowel movements and mood")

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("📝 Log Entry"):
        st.session_state.page = "Log Entry"
with c2:
    if st.button("📅 View Day"):
        st.session_state.page = "View Day"
with c3:
    if st.button("📈 View Trends"):
        st.session_state.page = "View Trends"

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
                    "entry_date": entry_date.isoformat(),
                    "amount_litres": float(amount_litres),
                    "drink_type": drink_type or None
                }).execute()
                st.success("Hydration entry saved.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif entry_type == "Sleep":
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-blue">😴 Sleep</div>', unsafe_allow_html=True)
        st.caption("Intended as one main sleep entry per day.")
        with st.form("sleep_form"):
            entry_date = st.date_input("Date", value=date.today(), key="sleep_date")
            sleep_hours = st.number_input("Sleep hours", min_value=0.0, step=0.5)
            sleep_quality = st.selectbox("Sleep quality", ["Poor", "OK", "Good", "Great"])
            submitted = st.form_submit_button("Save sleep entry")
            if submitted:
                supabase.table("sleep_entries").insert({
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

    food_df = filter_day(load_table("food_entries"), selected_day)
    hydration_df = filter_day(load_table("hydration_entries"), selected_day)
    sleep_df = filter_day(load_table("sleep_entries"), selected_day)
    bowel_df = filter_day(load_table("bowel_entries"), selected_day)
    mood_df = filter_day(load_table("mood_entries"), selected_day)

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
    display_day_table(
        food_df,
        ["id", "entry_date", "meal_type", "food_notes", "calories"],
        {"id": "ID", "entry_date": "Date", "meal_type": "Meal", "food_notes": "Food", "calories": "Calories"}
    )
    if not food_df.empty:
        food_options = {f"ID {int(r['id'])} - {r.get('meal_type', '')}": r for _, r in food_df.iterrows()}
        selected_food = st.selectbox("Select food entry", list(food_options.keys()), key="food_edit_select")
        row = food_options[selected_food]
        with st.form("food_edit_form"):
            edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key="food_edit_date")
            meal_list = ["Breakfast", "Lunch", "Dinner", "Snack"]
            edit_meal = st.selectbox("Meal type", meal_list, index=meal_list.index(row["meal_type"]) if row["meal_type"] in meal_list else 0, key="food_edit_meal")
            edit_notes = st.text_area("Food notes", value=row.get("food_notes") or "", key="food_edit_notes")
            edit_calories = st.number_input("Calories", min_value=0, step=10, value=int(row.get("calories") or 0), key="food_edit_calories")
            save_col, delete_col = st.columns(2)
            with save_col:
                save_food = st.form_submit_button("Save food changes")
            with delete_col:
                delete_food = st.form_submit_button("Delete food entry")
            if save_food:
                supabase.table("food_entries").update({
                    "entry_date": edit_date.isoformat(),
                    "meal_type": edit_meal,
                    "food_notes": edit_notes or None,
                    "calories": int(edit_calories)
                }).eq("id", int(row["id"])).execute()
                st.success("Food entry updated.")
                st.rerun()
            if delete_food:
                supabase.table("food_entries").delete().eq("id", int(row["id"])).execute()
                st.success("Food entry deleted.")
                st.rerun()

    st.markdown("### 💧 Hydration")
    display_day_table(
        hydration_df,
        ["id", "entry_date", "amount_litres", "drink_type"],
        {"id": "ID", "entry_date": "Date", "amount_litres": "Litres", "drink_type": "Drink"}
    )
    if not hydration_df.empty:
        hydration_options = {f"ID {int(r['id'])} - {r.get('drink_type') or 'Drink'}": r for _, r in hydration_df.iterrows()}
        selected_hydration = st.selectbox("Select hydration entry", list(hydration_options.keys()), key="hydration_edit_select")
        row = hydration_options[selected_hydration]
        with st.form("hydration_edit_form"):
            edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key="hydration_edit_date")
            edit_amount = st.number_input("Amount (litres)", min_value=0.0, step=0.1, value=float(row.get("amount_litres") or 0.0), key="hydration_edit_amount")
            edit_drink = st.text_input("Drink type", value=row.get("drink_type") or "", key="hydration_edit_drink")
            save_col, delete_col = st.columns(2)
            with save_col:
                save_hydration = st.form_submit_button("Save hydration changes")
            with delete_col:
                delete_hydration = st.form_submit_button("Delete hydration entry")
            if save_hydration:
                supabase.table("hydration_entries").update({
                    "entry_date": edit_date.isoformat(),
                    "amount_litres": float(edit_amount),
                    "drink_type": edit_drink or None
                }).eq("id", int(row["id"])).execute()
                st.success("Hydration entry updated.")
                st.rerun()
            if delete_hydration:
                supabase.table("hydration_entries").delete().eq("id", int(row["id"])).execute()
                st.success("Hydration entry deleted.")
                st.rerun()

    st.markdown("### 😴 Sleep")
    display_day_table(
        sleep_df,
        ["id", "entry_date", "sleep_hours", "sleep_quality"],
        {"id": "ID", "entry_date": "Date", "sleep_hours": "Hours", "sleep_quality": "Quality"}
    )
    if not sleep_df.empty:
        sleep_options = {f"ID {int(r['id'])} - {r.get('sleep_hours', 0)} hrs": r for _, r in sleep_df.iterrows()}
        selected_sleep = st.selectbox("Select sleep entry", list(sleep_options.keys()), key="sleep_edit_select")
        row = sleep_options[selected_sleep]
        with st.form("sleep_edit_form"):
            edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key="sleep_edit_date")
            edit_hours = st.number_input("Sleep hours", min_value=0.0, step=0.5, value=float(row.get("sleep_hours") or 0.0), key="sleep_edit_hours")
            qualities = ["Poor", "OK", "Good", "Great"]
            edit_quality = st.selectbox("Sleep quality", qualities, index=qualities.index(row["sleep_quality"]) if row.get("sleep_quality") in qualities else 0, key="sleep_edit_quality")
            save_col, delete_col = st.columns(2)
            with save_col:
                save_sleep = st.form_submit_button("Save sleep changes")
            with delete_col:
                delete_sleep = st.form_submit_button("Delete sleep entry")
            if save_sleep:
                supabase.table("sleep_entries").update({
                    "entry_date": edit_date.isoformat(),
                    "sleep_hours": float(edit_hours),
                    "sleep_quality": edit_quality
                }).eq("id", int(row["id"])).execute()
                st.success("Sleep entry updated.")
                st.rerun()
            if delete_sleep:
                supabase.table("sleep_entries").delete().eq("id", int(row["id"])).execute()
                st.success("Sleep entry deleted.")
                st.rerun()

    st.markdown("### 🩺 Bowel Movements")
    display_day_table(
        bowel_df,
        ["id", "entry_date", "event_time", "notes"],
        {"id": "ID", "entry_date": "Date", "event_time": "Time", "notes": "Notes"}
    )
    if not bowel_df.empty:
        bowel_options = {f"ID {int(r['id'])} - {r.get('event_time') or 'No time'}": r for _, r in bowel_df.iterrows()}
        selected_bowel = st.selectbox("Select bowel entry", list(bowel_options.keys()), key="bowel_edit_select")
        row = bowel_options[selected_bowel]
        with st.form("bowel_edit_form"):
            edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key="bowel_edit_date")
            edit_time = st.text_input("Time", value=row.get("event_time") or "", key="bowel_edit_time")
            edit_notes = st.text_area("Notes", value=row.get("notes") or "", key="bowel_edit_notes")
            save_col, delete_col = st.columns(2)
            with save_col:
                save_bowel = st.form_submit_button("Save bowel changes")
            with delete_col:
                delete_bowel = st.form_submit_button("Delete bowel entry")
            if save_bowel:
                supabase.table("bowel_entries").update({
                    "entry_date": edit_date.isoformat(),
                    "event_time": edit_time or None,
                    "notes": edit_notes or None
                }).eq("id", int(row["id"])).execute()
                st.success("Bowel entry updated.")
                st.rerun()
            if delete_bowel:
                supabase.table("bowel_entries").delete().eq("id", int(row["id"])).execute()
                st.success("Bowel entry deleted.")
                st.rerun()

    st.markdown("### 🙂 Mood")
    display_day_table(
        mood_df,
        ["id", "entry_date", "mood_rating", "notes"],
        {"id": "ID", "entry_date": "Date", "mood_rating": "Mood", "notes": "Notes"}
    )
    if not mood_df.empty:
        mood_options = {f"ID {int(r['id'])} - {r.get('mood_rating') or 'Mood'}": r for _, r in mood_df.iterrows()}
        selected_mood = st.selectbox("Select mood entry", list(mood_options.keys()), key="mood_edit_select")
        row = mood_options[selected_mood]
        moods = ["Very low", "Low", "OK", "Good", "Very good"]
        with st.form("mood_edit_form"):
            edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key="mood_edit_date")
            edit_rating = st.selectbox("Mood", moods, index=moods.index(row["mood_rating"]) if row.get("mood_rating") in moods else 0, key="mood_edit_rating")
            edit_notes = st.text_area("Notes", value=row.get("notes") or "", key="mood_edit_notes")
            save_col, delete_col = st.columns(2)
            with save_col:
                save_mood = st.form_submit_button("Save mood changes")
            with delete_col:
                delete_mood = st.form_submit_button("Delete mood entry")
            if save_mood:
                supabase.table("mood_entries").update({
                    "entry_date": edit_date.isoformat(),
                    "mood_rating": edit_rating,
                    "notes": edit_notes or None
                }).eq("id", int(row["id"])).execute()
                st.success("Mood entry updated.")
                st.rerun()
            if delete_mood:
                supabase.table("mood_entries").delete().eq("id", int(row["id"])).execute()
                st.success("Mood entry deleted.")
                st.rerun()

    policy_note()

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

    food_df = load_table("food_entries")
    hydration_df = load_table("hydration_entries")
    sleep_df = load_table("sleep_entries")
    bowel_df = load_table("bowel_entries")
    mood_df = load_table("mood_entries")

    def range_filter(df):
        if df.empty or "entry_date" not in df.columns:
            return pd.DataFrame()
        temp = df.copy()
        temp["entry_date"] = pd.to_datetime(temp["entry_date"])
        return temp[(temp["entry_date"].dt.date >= start_date) & (temp["entry_date"].dt.date <= end_date)]

    food_df = range_filter(food_df)
    hydration_df = range_filter(hydration_df)
    sleep_df = range_filter(sleep_df)
    bowel_df = range_filter(bowel_df)
    mood_df = range_filter(mood_df)

    st.markdown("### Food — calories by day")
    if not food_df.empty and "calories" in food_df.columns:
        daily = prepare_daily_series(food_df, "entry_date", "calories")
        daily = daily[(daily["entry_date"].dt.date >= start_date) & (daily["entry_date"].dt.date <= end_date)]
        fig = px.line(daily, x="entry_date", y="calories", markers=True)
        fig.update_traces(line=dict(color="#ff8c42", width=3))
        fig.update_xaxes(dtick="D", tickformat="%d %b")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No food data in this range.")

    st.markdown("### Hydration — litres by day")
    if not hydration_df.empty and "amount_litres" in hydration_df.columns:
        daily = prepare_daily_series(hydration_df, "entry_date", "amount_litres")
        daily = daily[(daily["entry_date"].dt.date >= start_date) & (daily["entry_date"].dt.date <= end_date)]
        fig = px.line(daily, x="entry_date", y="amount_litres", markers=True)
        fig.update_traces(line=dict(color="#ff5c8a", width=3))
        fig.update_xaxes(dtick="D", tickformat="%d %b")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hydration data in this range.")

    st.markdown("### Sleep — hours by day")
    if not sleep_df.empty and "sleep_hours" in sleep_df.columns:
        daily = prepare_daily_series(sleep_df, "entry_date", "sleep_hours")
        daily = daily[(daily["entry_date"].dt.date >= start_date) & (daily["entry_date"].dt.date <= end_date)]
        fig = px.line(daily, x="entry_date", y="sleep_hours", markers=True)
        fig.update_traces(line=dict(color="#5b5ce6", width=3))
        fig.update_xaxes(dtick="D", tickformat="%d %b")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sleep data in this range.")

    st.markdown("### Bowel movements — entries per day")
    if not bowel_df.empty:
        bowel_daily = bowel_df.groupby("entry_date", as_index=False).size()
        bowel_daily.columns = ["entry_date", "count"]
        fig = px.line(bowel_daily, x="entry_date", y="count", markers=True)
        fig.update_traces(line=dict(color="#20c997", width=3))
        fig.update_xaxes(dtick="D", tickformat="%d %b")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No bowel data in this range.")

    st.markdown("### Mood — entries per day")
    if not mood_df.empty:
        mood_daily = mood_df.groupby("entry_date", as_index=False).size()
        mood_daily.columns = ["entry_date", "count"]
        fig = px.line(mood_daily, x="entry_date", y="count", markers=True)
        fig.update_traces(line=dict(color="#845ef7", width=3))
        fig.update_xaxes(dtick="D", tickformat="%d %b")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No mood data in this range.")