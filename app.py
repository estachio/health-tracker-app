import streamlit as st
import pandas as pd
import plotly.express as px
import extra_streamlit_components as stx
from datetime import date, datetime, timedelta
from supabase_client import supabase


def apply_custom_styles():
    st.markdown("""
    <style>
    .stApp { background-color: #f4f7fb; }
    .block-container { max-width: 1000px; padding-top: 1.5rem; padding-bottom: 2rem; }

    h1, h2, h3, label, p, div, span {
        color: #1f1f1f;
    }

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
        color: #6c757d !important;
        margin-bottom: 8px;
        font-weight: 600;
    }

    .summary-value {
        font-size: 28px;
        font-weight: 700;
        color: #212529 !important;
    }

    .section-header-orange, .section-header-pink, .section-header-blue,
    .section-header-green, .section-header-purple, .section-header-dark {
        color: white !important;
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
        background-color: #1f2430;
        color: white !important;
        border: 1px solid #2f3542;
    }

    div.stButton > button p,
    div.stButton > button span,
    div.stFormSubmitButton > button p,
    div.stFormSubmitButton > button span {
        color: white !important;
    }

    input, textarea {
        color: #1f1f1f !important;
        background-color: white !important;
    }

    [data-baseweb="input"] input,
    [data-baseweb="base-input"] input,
    [data-baseweb="textarea"] textarea {
        color: #1f1f1f !important;
        -webkit-text-fill-color: #1f1f1f !important;
        background-color: white !important;
    }

    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-baseweb="base-input"] > div,
    [data-baseweb="textarea"] > div {
        background-color: white !important;
        color: #1f1f1f !important;
    }

    [role="listbox"] {
        background: white !important;
        color: #1f1f1f !important;
    }

    [role="option"] {
        background: white !important;
        color: #1f1f1f !important;
    }

    [role="option"]:hover {
        background: #f1f3f5 !important;
        color: #1f1f1f !important;
    }

    [role="option"] * {
        color: #1f1f1f !important;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)


class SimpleUser:
    def __init__(self, email, user_id):
        self.email = email
        self.id = user_id


def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="ht_cookie_manager")
    return st.session_state.cookie_manager


def save_login_cookie(user_email, user_id):
    cookie_manager = get_cookie_manager()
    expiry = datetime.utcnow() + timedelta(days=1)
    cookie_manager.set("ht_user_email", user_email, expires_at=expiry, key="set_ht_user_email")
    cookie_manager.set("ht_user_id", user_id, expires_at=expiry, key="set_ht_user_id")


def clear_login_cookie():
    cookie_manager = get_cookie_manager()
    cookie_manager.delete("ht_user_email", key="delete_ht_user_email")
    cookie_manager.delete("ht_user_id", key="delete_ht_user_id")


def restore_login_from_cookie():
    cookie_manager = get_cookie_manager()
    cookies = cookie_manager.get_all(key="get_all_cookies")
    if st.session_state.get("user") is None and cookies:
        cookie_email = cookies.get("ht_user_email")
        cookie_user_id = cookies.get("ht_user_id")
        if cookie_email and cookie_user_id:
            st.session_state.user = SimpleUser(cookie_email, cookie_user_id)


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


def prepare_daily_series(df, date_col, value_col, start_date=None, end_date=None):
    if date_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()

    working_df = df.copy()

    if working_df.empty:
        if start_date is None or end_date is None:
            return pd.DataFrame()
        full_date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        return pd.DataFrame({
            date_col: full_date_range,
            value_col: [0] * len(full_date_range)
        })

    working_df[date_col] = pd.to_datetime(working_df[date_col])

    daily = (
        working_df.groupby(date_col, as_index=False)[value_col]
        .sum()
        .sort_values(date_col)
    )

    start_date = pd.to_datetime(start_date) if start_date is not None else daily[date_col].min()
    end_date = pd.to_datetime(end_date) if end_date is not None else daily[date_col].max()

    full_date_range = pd.date_range(start=start_date, end=end_date, freq="D")
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


def show_flash_message():
    if st.session_state.flash_message:
        st.success(st.session_state.flash_message)
        st.session_state.flash_message = None


def build_selector_options(df, label_builder):
    options = []
    for _, row in df.iterrows():
        row_id = int(row["id"])
        label = label_builder(row)
        options.append((label, row_id))
    return options


def get_selected_row(df, selected_label, options):
    selected_id = dict(options)[selected_label]
    return df[df["id"].astype(int) == int(selected_id)].iloc[0]


st.set_page_config(page_title="Health Tracker", layout="wide")
apply_custom_styles()

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "View Day"
if "flash_message" not in st.session_state:
    st.session_state.flash_message = None

st.title("Health Tracker")

get_cookie_manager()
restore_login_from_cookie()
show_flash_message()

if st.session_state.user is None:
    st.caption("Sign up or log in to access your tracker")

    auth_tab1, auth_tab2 = st.tabs(["Log in", "Sign up"])

    with auth_tab1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-dark">Log in</div>', unsafe_allow_html=True)
        st.caption("Use your email address and password to sign in.")

        with st.form("login_form"):
            email = st.text_input("Email address", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_submitted = st.form_submit_button("Log in")

            if login_submitted:
                try:
                    result = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    st.session_state.user = result.user
                    save_login_cookie(result.user.email, result.user.id)
                    st.session_state.flash_message = "Logged in successfully."
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

    with auth_tab2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-dark">Sign up</div>', unsafe_allow_html=True)
        st.caption("Create an account to keep your tracker data private to you.")

        with st.form("signup_form"):
            signup_email = st.text_input("Email address", key="signup_email", placeholder="Enter your email")
            signup_password = st.text_input("Create password", type="password", key="signup_password", placeholder="Choose a password")
            signup_submitted = st.form_submit_button("Create account")

            if signup_submitted:
                try:
                    supabase.auth.sign_up({
                        "email": signup_email,
                        "password": signup_password
                    })
                    st.session_state.flash_message = "Account created. You can now log in."
                    st.rerun()
                except Exception as e:
                    st.error(f"Sign-up failed: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    user = require_auth()
    user_id = user.id

    st.caption(f"Logged in as {user.email}")

    top1, top2, top3 = st.columns([1, 1, 1])
    with top1:
        if st.button("📅 View Day"):
            st.session_state.page = "View Day"
    with top2:
        if st.button("📈 View Trends"):
            st.session_state.page = "View Trends"
    with top3:
        if st.button("Log out"):
            clear_login_cookie()
            st.session_state.user = None
            st.session_state.flash_message = "Logged out successfully."
            st.rerun()

    page = st.session_state.page

    if page == "View Day":
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

        # FOOD
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-orange">🍽️ Food</div>', unsafe_allow_html=True)

        with st.expander("Add food entry"):
            with st.form("food_form"):
                entry_date = st.date_input("Date", value=selected_day, key="food_date")
                meal_type = st.selectbox("Meal type", ["Breakfast", "Lunch", "Dinner", "Snack"], key="food_meal_type")
                food_notes = st.text_area("Food notes", key="food_notes")
                calories = st.number_input("Calories", min_value=0, step=10, key="food_calories")
                submitted = st.form_submit_button("Save food entry")
                if submitted:
                    supabase.table("food_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "meal_type": meal_type,
                        "food_notes": food_notes or None,
                        "calories": int(calories)
                    }).execute()
                    st.session_state.flash_message = "Food entry saved."
                    st.rerun()

        display_day_table(food_df, ["entry_date", "meal_type", "food_notes", "calories"], {
            "entry_date": "Date", "meal_type": "Meal", "food_notes": "Food", "calories": "Calories"
        })

        if not food_df.empty:
            food_options = build_selector_options(
                food_df,
                lambda r: f"{int(r['id'])} — {r.get('meal_type', '')} — {int(r.get('calories') or 0)} kcal"
            )
            selected_food = st.selectbox("Select food entry", [label for label, _ in food_options], key="food_edit_select")
            row = get_selected_row(food_df, selected_food, food_options)
            row_id = int(row["id"])

            with st.form(f"food_edit_form_{row_id}"):
                edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key=f"food_edit_date_{row_id}")
                meal_list = ["Breakfast", "Lunch", "Dinner", "Snack"]
                edit_meal = st.selectbox("Meal type", meal_list, index=meal_list.index(row["meal_type"]) if row["meal_type"] in meal_list else 0, key=f"food_edit_meal_{row_id}")
                edit_notes = st.text_area("Food notes", value=row.get("food_notes") or "", key=f"food_edit_notes_{row_id}")
                edit_calories = st.number_input("Calories", min_value=0, step=10, value=int(row.get("calories") or 0), key=f"food_edit_calories_{row_id}")

                c1, c2 = st.columns(2)
                with c1:
                    save_food = st.form_submit_button("Save food changes")
                with c2:
                    delete_food = st.form_submit_button("Delete food entry")

                if save_food:
                    supabase.table("food_entries").update({
                        "entry_date": edit_date.isoformat(),
                        "meal_type": edit_meal,
                        "food_notes": edit_notes or None,
                        "calories": int(edit_calories)
                    }).eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Food entry updated."
                    st.rerun()

                if delete_food:
                    supabase.table("food_entries").delete().eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Food entry deleted."
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # HYDRATION
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-pink">💧 Hydration</div>', unsafe_allow_html=True)

        with st.expander("Add hydration entry"):
            with st.form("hydration_form"):
                entry_date = st.date_input("Date", value=selected_day, key="hydration_date")
                amount_litres = st.number_input("Amount (litres)", min_value=0.0, step=0.1, key="hydration_amount")
                drink_type = st.text_input("Drink type", key="hydration_drink")
                submitted = st.form_submit_button("Save hydration entry")
                if submitted:
                    supabase.table("hydration_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "amount_litres": float(amount_litres),
                        "drink_type": drink_type or None
                    }).execute()
                    st.session_state.flash_message = "Hydration entry saved."
                    st.rerun()

        display_day_table(hydration_df, ["entry_date", "amount_litres", "drink_type"], {
            "entry_date": "Date", "amount_litres": "Litres", "drink_type": "Drink"
        })

        if not hydration_df.empty:
            hydration_options = build_selector_options(
                hydration_df,
                lambda r: f"{int(r['id'])} — {(r.get('drink_type') or 'Drink')} — {float(r.get('amount_litres') or 0):.1f} L"
            )
            selected_hydration = st.selectbox("Select hydration entry", [label for label, _ in hydration_options], key="hydration_edit_select")
            row = get_selected_row(hydration_df, selected_hydration, hydration_options)
            row_id = int(row["id"])

            with st.form(f"hydration_edit_form_{row_id}"):
                edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key=f"hydration_edit_date_{row_id}")
                edit_amount = st.number_input("Amount (litres)", min_value=0.0, step=0.1, value=float(row.get("amount_litres") or 0.0), key=f"hydration_edit_amount_{row_id}")
                edit_drink = st.text_input("Drink type", value=row.get("drink_type") or "", key=f"hydration_edit_drink_{row_id}")

                c1, c2 = st.columns(2)
                with c1:
                    save_hydration = st.form_submit_button("Save hydration changes")
                with c2:
                    delete_hydration = st.form_submit_button("Delete hydration entry")

                if save_hydration:
                    supabase.table("hydration_entries").update({
                        "entry_date": edit_date.isoformat(),
                        "amount_litres": float(edit_amount),
                        "drink_type": edit_drink or None
                    }).eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Hydration entry updated."
                    st.rerun()

                if delete_hydration:
                    supabase.table("hydration_entries").delete().eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Hydration entry deleted."
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # SLEEP
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-blue">😴 Sleep</div>', unsafe_allow_html=True)

        with st.expander("Add sleep entry"):
            with st.form("sleep_form"):
                entry_date = st.date_input("Date", value=selected_day, key="sleep_date")
                sleep_hours = st.number_input("Sleep hours", min_value=0.0, step=0.5, key="sleep_hours")
                sleep_quality = st.selectbox("Sleep quality", ["Poor", "OK", "Good", "Great"], key="sleep_quality")
                submitted = st.form_submit_button("Save sleep entry")
                if submitted:
                    supabase.table("sleep_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "sleep_hours": float(sleep_hours),
                        "sleep_quality": sleep_quality
                    }).execute()
                    st.session_state.flash_message = "Sleep entry saved."
                    st.rerun()

        display_day_table(sleep_df, ["entry_date", "sleep_hours", "sleep_quality"], {
            "entry_date": "Date", "sleep_hours": "Hours", "sleep_quality": "Quality"
        })

        if not sleep_df.empty:
            sleep_options = build_selector_options(
                sleep_df,
                lambda r: f"{int(r['id'])} — {float(r.get('sleep_hours') or 0):.1f} hrs — {r.get('sleep_quality') or ''}"
            )
            selected_sleep = st.selectbox("Select sleep entry", [label for label, _ in sleep_options], key="sleep_edit_select")
            row = get_selected_row(sleep_df, selected_sleep, sleep_options)
            row_id = int(row["id"])

            with st.form(f"sleep_edit_form_{row_id}"):
                edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key=f"sleep_edit_date_{row_id}")
                edit_hours = st.number_input("Sleep hours", min_value=0.0, step=0.5, value=float(row.get("sleep_hours") or 0.0), key=f"sleep_edit_hours_{row_id}")
                qualities = ["Poor", "OK", "Good", "Great"]
                edit_quality = st.selectbox("Sleep quality", qualities, index=qualities.index(row["sleep_quality"]) if row.get("sleep_quality") in qualities else 0, key=f"sleep_edit_quality_{row_id}")

                c1, c2 = st.columns(2)
                with c1:
                    save_sleep = st.form_submit_button("Save sleep changes")
                with c2:
                    delete_sleep = st.form_submit_button("Delete sleep entry")

                if save_sleep:
                    supabase.table("sleep_entries").update({
                        "entry_date": edit_date.isoformat(),
                        "sleep_hours": float(edit_hours),
                        "sleep_quality": edit_quality
                    }).eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Sleep entry updated."
                    st.rerun()

                if delete_sleep:
                    supabase.table("sleep_entries").delete().eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Sleep entry deleted."
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # BOWEL
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-green">🩺 Bowel Movement</div>', unsafe_allow_html=True)

        with st.expander("Add bowel entry"):
            with st.form("bowel_form"):
                entry_date = st.date_input("Date", value=selected_day, key="bowel_date")
                event_time = st.text_input("Time", placeholder="e.g. 07:30", key="bowel_time")
                notes = st.text_area("Notes", key="bowel_notes")
                submitted = st.form_submit_button("Save bowel entry")
                if submitted:
                    supabase.table("bowel_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "event_time": event_time or None,
                        "notes": notes or None
                    }).execute()
                    st.session_state.flash_message = "Bowel entry saved."
                    st.rerun()

        display_day_table(bowel_df, ["entry_date", "event_time", "notes"], {
            "entry_date": "Date", "event_time": "Time", "notes": "Notes"
        })

        if not bowel_df.empty:
            bowel_options = build_selector_options(
                bowel_df,
                lambda r: f"{int(r['id'])} — {(r.get('event_time') or 'No time')} — {(r.get('notes') or '')[:20]}"
            )
            selected_bowel = st.selectbox("Select bowel entry", [label for label, _ in bowel_options], key="bowel_edit_select")
            row = get_selected_row(bowel_df, selected_bowel, bowel_options)
            row_id = int(row["id"])

            with st.form(f"bowel_edit_form_{row_id}"):
                edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key=f"bowel_edit_date_{row_id}")
                edit_time = st.text_input("Time", value=row.get("event_time") or "", key=f"bowel_edit_time_{row_id}")
                edit_notes = st.text_area("Notes", value=row.get("notes") or "", key=f"bowel_edit_notes_{row_id}")

                c1, c2 = st.columns(2)
                with c1:
                    save_bowel = st.form_submit_button("Save bowel changes")
                with c2:
                    delete_bowel = st.form_submit_button("Delete bowel entry")

                if save_bowel:
                    supabase.table("bowel_entries").update({
                        "entry_date": edit_date.isoformat(),
                        "event_time": edit_time or None,
                        "notes": edit_notes or None
                    }).eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Bowel entry updated."
                    st.rerun()

                if delete_bowel:
                    supabase.table("bowel_entries").delete().eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Bowel entry deleted."
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # MOOD
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header-purple">🙂 Mood</div>', unsafe_allow_html=True)

        with st.expander("Add mood entry"):
            with st.form("mood_form"):
                entry_date = st.date_input("Date", value=selected_day, key="mood_date")
                mood_rating = st.selectbox("Mood", ["Very low", "Low", "OK", "Good", "Very good"], key="mood_rating")
                notes = st.text_area("Notes", key="mood_notes")
                submitted = st.form_submit_button("Save mood entry")
                if submitted:
                    supabase.table("mood_entries").insert({
                        "user_id": user_id,
                        "entry_date": entry_date.isoformat(),
                        "mood_rating": mood_rating,
                        "notes": notes or None
                    }).execute()
                    st.session_state.flash_message = "Mood entry saved."
                    st.rerun()

        display_day_table(mood_df, ["entry_date", "mood_rating", "notes"], {
            "entry_date": "Date", "mood_rating": "Mood", "notes": "Notes"
        })

        if not mood_df.empty:
            mood_options = build_selector_options(
                mood_df,
                lambda r: f"{int(r['id'])} — {r.get('mood_rating') or ''} — {(r.get('notes') or '')[:20]}"
            )
            selected_mood = st.selectbox("Select mood entry", [label for label, _ in mood_options], key="mood_edit_select")
            row = get_selected_row(mood_df, selected_mood, mood_options)
            row_id = int(row["id"])

            with st.form(f"mood_edit_form_{row_id}"):
                edit_date = st.date_input("Date", value=pd.to_datetime(row["entry_date"]).date(), key=f"mood_edit_date_{row_id}")
                moods = ["Very low", "Low", "OK", "Good", "Very good"]
                edit_rating = st.selectbox("Mood", moods, index=moods.index(row["mood_rating"]) if row.get("mood_rating") in moods else 0, key=f"mood_edit_rating_{row_id}")
                edit_notes = st.text_area("Notes", value=row.get("notes") or "", key=f"mood_edit_notes_{row_id}")

                c1, c2 = st.columns(2)
                with c1:
                    save_mood = st.form_submit_button("Save mood changes")
                with c2:
                    delete_mood = st.form_submit_button("Delete mood entry")

                if save_mood:
                    supabase.table("mood_entries").update({
                        "entry_date": edit_date.isoformat(),
                        "mood_rating": edit_rating,
                        "notes": edit_notes or None
                    }).eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Mood entry updated."
                    st.rerun()

                if delete_mood:
                    supabase.table("mood_entries").delete().eq("id", row_id).eq("user_id", user_id).execute()
                    st.session_state.flash_message = "Mood entry deleted."
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

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
        food_daily = prepare_daily_series(food_df, "entry_date", "calories", start_date, end_date)
        if not food_daily.empty:
            fig = px.line(food_daily, x="entry_date", y="calories", markers=True)
            fig.update_traces(line=dict(color="#ff8c42", width=3, shape="spline"))
            fig.update_xaxes(range=[pd.to_datetime(start_date), pd.to_datetime(end_date)], dtick="D", tickformat="%d %b")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No food data in this range.")

        st.markdown("### Hydration — litres by day")
        hydration_daily = prepare_daily_series(hydration_df, "entry_date", "amount_litres", start_date, end_date)
        if not hydration_daily.empty:
            fig = px.line(hydration_daily, x="entry_date", y="amount_litres", markers=True)
            fig.update_traces(line=dict(color="#ff5c8a", width=3, shape="spline"))
            fig.update_xaxes(range=[pd.to_datetime(start_date), pd.to_datetime(end_date)], dtick="D", tickformat="%d %b")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hydration data in this range.")

        st.markdown("### Sleep — hours by day")
        sleep_daily = prepare_daily_series(sleep_df, "entry_date", "sleep_hours", start_date, end_date)
        if not sleep_daily.empty:
            fig = px.line(sleep_daily, x="entry_date", y="sleep_hours", markers=True)
            fig.update_traces(line=dict(color="#5b5ce6", width=3, shape="spline"))
            fig.update_xaxes(range=[pd.to_datetime(start_date), pd.to_datetime(end_date)], dtick="D", tickformat="%d %b")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sleep data in this range.")

        st.markdown("### Bowel movements — entries per day")
        if not bowel_df.empty:
            bowel_daily = bowel_df.groupby("entry_date", as_index=False).size()
            bowel_daily.columns = ["entry_date", "count"]
        else:
            bowel_daily = pd.DataFrame(columns=["entry_date", "count"])

        bowel_daily = prepare_daily_series(bowel_daily, "entry_date", "count", start_date, end_date)
        if not bowel_daily.empty:
            fig = px.line(bowel_daily, x="entry_date", y="count", markers=True)
            fig.update_traces(line=dict(color="#20c997", width=3, shape="spline"))
            fig.update_xaxes(range=[pd.to_datetime(start_date), pd.to_datetime(end_date)], dtick="D", tickformat="%d %b")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No bowel data in this range.")

        st.markdown("### Mood — entries per day")
        if not mood_df.empty:
            mood_daily = mood_df.groupby("entry_date", as_index=False).size()
            mood_daily.columns = ["entry_date", "count"]
        else:
            mood_daily = pd.DataFrame(columns=["entry_date", "count"])

        mood_daily = prepare_daily_series(mood_daily, "entry_date", "count", start_date, end_date)
        if not mood_daily.empty:
            fig = px.line(mood_daily, x="entry_date", y="count", markers=True)
            fig.update_traces(line=dict(color="#845ef7", width=3, shape="spline"))
            fig.update_xaxes(range=[pd.to_datetime(start_date), pd.to_datetime(end_date)], dtick="D", tickformat="%d %b")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No mood data in this range.")