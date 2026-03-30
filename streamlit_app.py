import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st
import json
import hashlib

USER_LIST_DIR = pathlib.Path("data/user_lists")
USER_RATING_DIR = pathlib.Path("data/user_ratings")
ACCOUNT_PATH = pathlib.Path("data/user_accounts.json")
DATA_PATH = pathlib.Path("data/steam_data_complete.csv")

st.set_page_config(page_title="Steam Indie Insights",
                   page_icon="🎮", layout="wide")

PRIMARY = "#5b8def"
ACCENT = "#8f53ff"
DARK = "#0f172a"
LIGHT = "#f5f7fb"

st.markdown(
    """
    <style>
    /* Force dark mode for both themes */
    :root { --primary-color: #22c55e; }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
        background-color: #0f172a !important; 
    }
    .main { background: linear-gradient(180deg, rgba(15,23,42,0.9) 0%, rgba(15,23,42,0.96) 40%, #0b1224 100%) !important; color: #e6e9f2 !important; }
    body, .stApp, p, span, div, label, input, textarea, select, h1, h2, h3, h4, h5, h6 { color: #e6e9f2 !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #e6e9f2 !important; }
    .stMetric label { color: #c7d1e0 !important; font-size: 0.9rem; }
    .stMetric div[data-testid="stMetricValue"] { color: white !important; font-weight: 700; }
    .block-title { font-size: 1.2rem; font-weight: 700; color: PRIMARY_COLOR; text-transform: uppercase; letter-spacing: 0.05em; }
    .pill { display: inline-block; padding: 0.3rem 0.7rem; border-radius: 999px; background: rgba(143,83,255,0.15); color: #e5d8ff; margin-right: 0.25rem; font-size: 0.85rem; }
    .card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1rem 1.2rem; box-shadow: 0 8px 30px rgba(0,0,0,0.25); }
    .hero { background: radial-gradient(ellipse at 20% 20%, rgba(91,141,239,0.18), transparent 35%),
                     radial-gradient(ellipse at 80% 0%, rgba(143,83,255,0.22), transparent 30%),
                     linear-gradient(120deg, rgba(91,141,239,0.14), rgba(143,83,255,0.12));
             border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 1.4rem 1.6rem; }
    .hero h1 { margin: 0; color: white !important; font-size: 2.2rem; letter-spacing: 0.02em; }
    .hero p { color: #d4ddf0 !important; font-size: 1rem; margin-top: 0.4rem; }
    .stButton>button { background: linear-gradient(120deg, #22c55e, #1a9b4f) !important; border: 1px solid #178341 !important; color: #0b1b10 !important; }
    .stButton>button:hover { background: linear-gradient(120deg, #1fa64f, #178341) !important; border-color: #137235 !important; color: #e6f4ea !important; }
    [data-baseweb="slider"] [role="slider"] { background-color: #22c55e !important; border-color: #178341 !important; }
    [data-baseweb="slider"] [role="slider"]:hover { box-shadow: 0 0 0 6px rgba(34,197,94,0.18) !important; }
    </style>
    """.replace("PRIMARY_COLOR", PRIMARY),
    unsafe_allow_html=True,
)

USER_LIST_DIR.mkdir(parents=True, exist_ok=True)
USER_RATING_DIR.mkdir(parents=True, exist_ok=True)
ACCOUNT_PATH.parent.mkdir(parents=True, exist_ok=True)


def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def _safe_username(raw: str) -> str:
    return "".join(ch for ch in raw.strip() if ch.isalnum() or ch in ("-", "_"))


def load_user_list(username: str) -> list:
    safe_name = _safe_username(username)
    path = USER_LIST_DIR / f"{safe_name}.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_user_list(username: str, games: list) -> None:
    safe_name = _safe_username(username)
    path = USER_LIST_DIR / f"{safe_name}.json"
    path.write_text(json.dumps(games, ensure_ascii=False,
                    indent=2), encoding="utf-8")


def load_user_ratings(username: str) -> dict:
    safe_name = _safe_username(username)
    path = USER_RATING_DIR / f"{safe_name}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_user_ratings(username: str, ratings: dict) -> None:
    safe_name = _safe_username(username)
    path = USER_RATING_DIR / f"{safe_name}.json"
    path.write_text(json.dumps(ratings, ensure_ascii=False,
                    indent=2), encoding="utf-8")


def load_accounts() -> dict:
    if not ACCOUNT_PATH.exists():
        return {}
    try:
        return json.loads(ACCOUNT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_accounts(accounts: dict) -> None:
    ACCOUNT_PATH.write_text(json.dumps(
        accounts, ensure_ascii=False, indent=2), encoding="utf-8")


def create_account(username: str, password: str) -> tuple[bool, str]:
    if not username.strip() or not password:
        return False, "Username and password are required."
    user_key = _safe_username(username)
    accounts = load_accounts()
    if user_key in accounts:
        return False, "User already exists."
    accounts[user_key] = _hash_pw(password)
    save_accounts(accounts)
    return True, user_key


def verify_account(username: str, password: str) -> tuple[bool, str]:
    user_key = _safe_username(username)
    accounts = load_accounts()
    if user_key not in accounts:
        return False, "User not found."
    if accounts[user_key] != _hash_pw(password):
        return False, "Incorrect password."
    return True, user_key


if not DATA_PATH.exists():
    st.error("Dataset not found. Please run merge_awards_data.py to generate data/steam_data_complete.csv.")
    st.stop()

df_raw = pd.read_csv(DATA_PATH, sep=";")
if "genres_list" in df_raw.columns:
    df_raw["is_indie"] = df_raw["genres_list"].apply(
        lambda x: "Indie" in str(x))
else:
    df_raw["is_indie"] = df_raw.get("is_indie", 0)
if "release_year" not in df_raw.columns and "release_date" in df_raw.columns:
    df_raw["release_year"] = pd.to_datetime(
        df_raw["release_date"], errors="coerce").dt.year

# Create filtered version for Information tab (exclude 2020 and earlier games)
df = df_raw.copy()
if "release_year" in df.columns:
    df = df[df["release_year"] >= 2021]

if "user" not in st.session_state:
    st.session_state["user"] = ""
if "user_games" not in st.session_state:
    st.session_state["user_games"] = []
if "user_ratings" not in st.session_state:
    st.session_state["user_ratings"] = {}

price_min = float(df["price"].min()) if "price" in df else 0.0
price_max = float(df["price"].max()) if "price" in df else 100.0
year_min = max(2021, int(df["release_year"].min())
               ) if "release_year" in df else 2021
year_max = int(df["release_year"].max()) if "release_year" in df else 2025

st.sidebar.header("🎮 Explore")
st.sidebar.subheader("👤 Account")
auth_mode = st.sidebar.radio(
    "Mode", ["Sign in", "Sign up"], index=0, horizontal=True)

if auth_mode == "Sign in":
    login_user = st.sidebar.text_input("Username", key="login_username")
    login_pw = st.sidebar.text_input(
        "Password", type="password", key="login_pw")
    if st.sidebar.button("Sign in"):
        ok, msg = verify_account(login_user, login_pw)
        if ok:
            st.session_state["user"] = msg
            st.session_state["user_games"] = load_user_list(msg)
            st.session_state["user_ratings"] = load_user_ratings(msg)
            st.sidebar.success(f"Signed in as {msg}")
        else:
            st.sidebar.error(msg)

if auth_mode == "Sign up":
    st.markdown("## ✨ Create Your Account")
    st.caption(
        "Local-only demo auth. Passwords are hashed but not production-grade.")
    with st.form("signup_form"):
        new_user = st.text_input("Username", key="signup_username")
        new_pw = st.text_input("Password", type="password", key="signup_pw")
        new_pw2 = st.text_input(
            "Confirm password", type="password", key="signup_pw2")
        submitted = st.form_submit_button("Create account")
        if submitted:
            if not new_user.strip() or not new_pw or not new_pw2:
                st.error("All fields are required.")
            elif new_pw != new_pw2:
                st.error("Passwords do not match.")
            else:
                ok, msg = create_account(new_user, new_pw)
                if ok:
                    st.session_state["user"] = msg
                    st.session_state["user_games"] = load_user_list(msg)
                    st.session_state["user_ratings"] = load_user_ratings(msg)
                    st.success(f"Account created and signed in as {msg}.")
                else:
                    st.error(msg)

active_user = st.session_state.get("user", "") or ""
user_games = st.session_state.get("user_games", [])
ratings_map = st.session_state.get("user_ratings", {})
user_game_names = sorted(user_games)
# Use unfiltered df_raw for user library to show all their games
user_games_full_df = df_raw[df_raw["name"].isin(user_games)].copy(
) if "name" in df_raw.columns else pd.DataFrame()

if active_user:
    if st.sidebar.button("Sign out"):
        st.session_state["user"] = ""
        st.session_state["user_games"] = []
        st.session_state["user_ratings"] = {}
        active_user = ""
        st.sidebar.success("Signed out.")

insights_tab, library_tab, awards_tab = st.tabs(
    ["📊 Information", "📚 My Stats", "🏆 Awards"])

with insights_tab:
    st.markdown('<div class="hero"><h1>🎮 Steam Indie Insights</h1><p>Exploring how indie games have evolved between 2021-2025: market trends, genre popularity, price impact on engagement, and growing recognition in Steam Awards.</p></div>', unsafe_allow_html=True)
    st.markdown(" ")

    st.markdown("### 🔍 Filters")
    st.markdown(" ")

    segment_options = ["Indie and Non-Indie", "Indie", "Non-Indie"]
    f1, f2, f3 = st.columns(3)
    segment = f1.selectbox(
        "Segment",
        segment_options,
        index=1 if "is_indie" in df.columns else 0,
    )
    price_range = f2.slider(
        "Price range",
        min_value=price_min,
        max_value=100.0,
        value=(price_min, min(price_max, 50.0)),
        step=0.5,
    )
    year_range = f3.slider(
        "Release year",
        min_value=year_min,
        max_value=year_max,
        value=(max(year_min, year_max - 10), year_max),
        step=1,
    )

    filtered = df.copy()
    if "price" in filtered:
        filtered = filtered[(filtered["price"] >= price_range[0])
                            & (filtered["price"] <= price_range[1])]
    if "release_year" in filtered:
        filtered = filtered[(filtered["release_year"] >= year_range[0]) & (
            filtered["release_year"] <= year_range[1])]
    if "is_indie" in filtered:
        filtered["segment"] = filtered["is_indie"].apply(
            lambda x: "Indie" if x else "Non-Indie")
        if segment != "Indie and Non-Indie":
            filtered = filtered[filtered["segment"] == segment]

    filtered_segment = filtered.copy()

    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Games", f"{len(filtered_segment):,}")
    col2.metric("💰 Average Price",
                f"${filtered_segment['price'].mean():.2f}" if "price" in filtered_segment else "-")
    col3.metric(
        "⭐ Average Recs", f"{filtered_segment['recommendations'].mean():,.0f}" if "recommendations" in filtered_segment else "-")

    c_top1, c_top2 = st.columns(2)
    if not filtered_segment.empty and "release_year" in filtered_segment.columns:
        yearly = (
            filtered_segment
            .groupby(["release_year", "segment"])
            .agg(avg_price=("price", "mean"), median_price=("price", "median"))
            .reset_index()
        )
        fig_avg = px.line(
            yearly,
            x="release_year",
            y="avg_price",
            color="segment",
            markers=True,
            color_discrete_map={"Indie": ACCENT, "Non-Indie": PRIMARY},
            title="📈 Average Price by Year",
        )
        fig_med = px.line(
            yearly,
            x="release_year",
            y="median_price",
            color="segment",
            markers=True,
            color_discrete_map={"Indie": ACCENT, "Non-Indie": PRIMARY},
            title="📊 Median Price by Year",
        )
        c_top1.plotly_chart(fig_avg, use_container_width=True)
        c_top2.plotly_chart(fig_med, use_container_width=True)
    else:
        c_top1.info("Add release_year to see the price trend.")
        c_top2.info("Add release_year to see the median trend.")

    c_mid1, c_mid2 = st.columns(2)
    if "recommendations" in filtered_segment and "price" in filtered_segment:
        fig_scatter = px.scatter(
            filtered_segment,
            x="price",
            y="recommendations",
            color="segment",
            color_discrete_map={"Indie": ACCENT, "Non-Indie": PRIMARY},
            hover_data=[
                "name", "developer"] if "name" in filtered_segment else None,
            title="💵 Price vs ⭐ Recommendations",
            log_y=True,
        )
        c_mid1.plotly_chart(fig_scatter, use_container_width=True)
    else:
        c_mid1.info("Need price and recommendations columns for this chart.")

    if "primary_genre" in filtered_segment:
        top_genres = (
            filtered_segment[filtered_segment["primary_genre"].notna()]
            .groupby(["primary_genre", "segment"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(20)
        )
        fig_genre = px.bar(
            top_genres,
            x="count",
            y="primary_genre",
            color="segment",
            color_discrete_map={"Indie": ACCENT, "Non-Indie": PRIMARY},
            orientation="h",
            title="🎭 Top Genres",
        )
        c_mid2.plotly_chart(fig_genre, use_container_width=True)
    else:
        c_mid2.info("primary_genre column not found.")

    c_bot1, c_bot2 = st.columns(2)
    if "recommendations" in filtered_segment:
        fig_hist = px.histogram(
            filtered_segment,
            x="recommendations",
            color="segment",
            nbins=50,
            log_y=True,
            color_discrete_map={"Indie": ACCENT, "Non-Indie": PRIMARY},
            title="📊 Recommendations Distribution",
        )
        c_bot1.plotly_chart(fig_hist, use_container_width=True)
    else:
        c_bot1.info("recommendations column not found.")

with library_tab:
    if not active_user:
        st.info("Sign in to manage your library and ratings.")
    else:
        st.markdown("## 👤 Your Info")
        st.caption("Manage your saved games and ratings in one place.")
        st.markdown("### ➕ Add Games to Your Library")
        indie_titles = []
        if "name" in df_raw.columns and "is_indie" in df_raw.columns:
            indie_titles = sorted(
                df_raw[df_raw["is_indie"] == True]["name"].dropna().unique())
        add_selection = st.multiselect(
            "Add games to your library",
            indie_titles,
            key="add_games",
            help="Pick titles to add; selection clears after saving.",
        )
        if st.button("Add to my list", key="add_to_list_main"):
            if add_selection:
                existing = set(st.session_state.get("user_games", []))
                updated = sorted(existing.union(add_selection))
                st.session_state["user_games"] = updated
                save_user_list(active_user, updated)
                if "add_games" in st.session_state:
                    try:
                        st.session_state["add_games"].clear()
                    except Exception:
                        pass
                st.success("Added to your library.")
            else:
                st.info("Select games to add.")

        if not user_games_full_df.empty:
            st.markdown("### 📊 Your Library Insights")
            c_lib1, c_lib2 = st.columns(2)

            if "release_year" in user_games_full_df:
                year_counts = (
                    user_games_full_df[user_games_full_df["release_year"].notna()]
                    .groupby("release_year")
                    .size()
                    .reset_index(name="games")
                    .sort_values("release_year")
                )
                fig_user_year = px.bar(
                    year_counts,
                    x="release_year",
                    y="games",
                    title="📅 Games by Release Year (Your Library)",
                    color_discrete_sequence=[ACCENT],
                )
                c_lib1.plotly_chart(fig_user_year, use_container_width=True)
            else:
                c_lib1.info("No release year data for your games.")

            if ratings_map:
                ratings_df = user_games_full_df.copy()
                ratings_df["your_rating"] = ratings_df["name"].map(ratings_map)
                ratings_df["your_rating"] = pd.to_numeric(
                    ratings_df["your_rating"], errors="coerce")
                ratings_df = ratings_df[ratings_df["your_rating"].notna()]
                if not ratings_df.empty:
                    fig_user_ratings = px.histogram(
                        ratings_df,
                        x="your_rating",
                        nbins=10,
                        color_discrete_sequence=["#22c55e"],
                        title="⭐ Your Rating Distribution",
                    )
                    c_lib2.plotly_chart(
                        fig_user_ratings, use_container_width=True)
                else:
                    c_lib2.info("Rate some games to see this.")
            else:
                c_lib2.info("Rate some games to see this.")

        st.markdown("### 🎯 Save or Update a Rating")
        if user_game_names:
            target_game = st.selectbox(
                "Select a game from your library", user_game_names, key="rating_select")
            current_rating = ratings_map.get(target_game, 0)
            new_rating = st.slider(
                "Your rating (0-10)", 0.0, 10.0, float(current_rating), 0.5, key="rating_slider")
            if st.button("Save rating", key="save_rating"):
                ratings_map[target_game] = new_rating
                st.session_state["user_ratings"] = ratings_map
                save_user_ratings(active_user, ratings_map)
                st.success("Rating saved.")
        else:
            st.info("Add games to your library to start rating them.")

        st.markdown("### 💾 Your Saved Games")
        if user_games_full_df.empty:
            st.info("No saved games yet.")
        else:
            table = user_games_full_df[[
                "name", "release_year", "price", "recommendations"]].copy()
            table.insert(0, "#", range(1, len(table) + 1))
            st.dataframe(table, use_container_width=True)

with awards_tab:
    st.markdown('<div class="hero"><h1>🏆 Steam Awards Analysis</h1><p>Are indie games starting to be more noticed in awards? Explore nomination trends, win rates, and recognition patterns across categories from 2021-2025.</p></div>', unsafe_allow_html=True)
    st.markdown(" ")

    # Check if awards columns exist
    has_awards_data = "has_awards" in df_raw.columns and "total_wins" in df_raw.columns

    if not has_awards_data:
        st.warning(
            "Awards data not available. Please run the data processing notebook to merge Steam Awards data.")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🎮 Games with Nominations",
                    f"{df_raw['has_awards'].sum():,}")
        col2.metric("🏆 Award Winners", f"{df_raw['is_award_winner'].sum():,}")
        col3.metric("🎯 Total Nominations",
                    f"{df_raw['total_nominations'].sum():,}")
        col4.metric("🏅 Total Wins", f"{df_raw['total_wins'].sum():,}")

        st.markdown("---")

        # Indie vs Non-Indie Awards Over Time
        st.markdown("### 📈 Indie vs Non-Indie: Awards Through the Years")

        # Load raw awards CSV directly for accurate counting
        awards_csv_path = pathlib.Path("data/steam_awards_nominees.csv")
        if awards_csv_path.exists():
            awards_raw = pd.read_csv(awards_csv_path)

            # Merge with database to get is_indie information
            awards_with_segment = awards_raw.merge(
                df_raw[['name', 'is_indie']],
                left_on='game',
                right_on='name',
                how='left'
            )

            # Fill missing is_indie with False (assume non-indie if not in our database)
            awards_with_segment['is_indie'] = awards_with_segment['is_indie'].fillna(
                False)
            awards_with_segment['segment'] = awards_with_segment['is_indie'].apply(
                lambda x: 'Indie' if x else 'Non-Indie'
            )

            # Aggregate by year and segment
            yearly_awards = awards_with_segment.groupby(['year', 'segment']).agg({
                'is_winner': 'sum',  # Sum of 1s = count of wins
                'game': 'count'  # Total nominations
            }).reset_index()
            yearly_awards.columns = [
                'award_year', 'segment', 'total_wins', 'total_nominations']

            c1, c2 = st.columns(2)

            with c1:
                # Nominations over time
                fig_nom = px.line(
                    yearly_awards,
                    x='award_year',
                    y='total_nominations',
                    color='segment',
                    markers=True,
                    color_discrete_map={'Indie': ACCENT, 'Non-Indie': PRIMARY},
                    title='🎯 Total Nominations by Award Year',
                    labels={'total_nominations': 'Nominations',
                            'award_year': 'Award Year'}
                )
                fig_nom.update_layout(legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_nom, use_container_width=True)

            with c2:
                # Wins over time
                fig_wins = px.line(
                    yearly_awards,
                    x='award_year',
                    y='total_wins',
                    color='segment',
                    markers=True,
                    color_discrete_map={'Indie': ACCENT, 'Non-Indie': PRIMARY},
                    title='🏆 Total Wins by Award Year',
                    labels={'total_wins': 'Wins',
                            'award_year': 'Award Year'}
                )
                fig_wins.update_layout(legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_wins, use_container_width=True)

            # Games nominated over time
            games_by_year = awards_with_segment.groupby(['year', 'segment'])[
                'game'].nunique().reset_index(name='games_nominated')
            games_by_year.columns = [
                'award_year', 'segment', 'games_nominated']

            fig_games = px.bar(
                games_by_year,
                x='award_year',
                y='games_nominated',
                color='segment',
                barmode='group',
                color_discrete_map={'Indie': ACCENT, 'Non-Indie': PRIMARY},
                title='🎮 Number of Games Nominated by Award Year',
                labels={'games_nominated': 'Games',
                        'award_year': 'Award Year'}
            )
            fig_games.update_layout(legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_games, use_container_width=True)
        else:
            st.warning(
                "Steam Awards CSV file not found. Please ensure data/steam_awards_nominees.csv exists.")

        st.markdown("---")

        # Genre Analysis
        st.markdown("### 🎭 Genres That Get the Most Nominations")

        # Filter games with awards and genres
        genre_awards = df_raw[(df_raw['has_awards'] == 1) & (
            df_raw['genres_list'].notna())].copy()

        if not genre_awards.empty:
            # Expand genres
            genre_rows = []
            for _, row in genre_awards.iterrows():
                try:
                    # Handle genres_list - might be string representation of list
                    genres = eval(row['genres_list']) if isinstance(
                        row['genres_list'], str) else row['genres_list']
                    if isinstance(genres, list):
                        for genre in genres:
                            if genre and genre.strip():
                                genre_rows.append({
                                    'genre': genre.strip(),
                                    'nominations': row['total_nominations'],
                                    'wins': row['total_wins'],
                                    'is_indie': row['is_indie']
                                })
                except:
                    pass

            if genre_rows:
                genre_df = pd.DataFrame(genre_rows)
                genre_df['segment'] = genre_df['is_indie'].apply(
                    lambda x: 'Indie' if x else 'Non-Indie')

                c3, c4 = st.columns(2)

                with c3:
                    # Top genres by total nominations
                    genre_nom = genre_df.groupby('genre')['nominations'].sum(
                    ).sort_values(ascending=False).head(15).reset_index()

                    fig_genre_nom = px.bar(
                        genre_nom,
                        x='nominations',
                        y='genre',
                        orientation='h',
                        color_discrete_sequence=[ACCENT],
                        title='🎯 Top 15 Genres by Total Nominations'
                    )
                    fig_genre_nom.update_layout(
                        yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_genre_nom, use_container_width=True)

                with c4:
                    # Top genres by total wins
                    genre_wins = genre_df.groupby('genre')['wins'].sum(
                    ).sort_values(ascending=False).head(15).reset_index()

                    fig_genre_wins = px.bar(
                        genre_wins,
                        x='wins',
                        y='genre',
                        orientation='h',
                        color_discrete_sequence=['#22c55e'],
                        title='🏅 Top 15 Genres by Total Wins'
                    )
                    fig_genre_wins.update_layout(
                        yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_genre_wins, use_container_width=True)

                # Genre nominations by segment
                st.markdown("### Genre Performance: Indie vs Non-Indie")

                genre_segment = genre_df.groupby(['genre', 'segment'])[
                    'nominations'].sum().reset_index()
                top_genres_list = genre_df.groupby('genre')['nominations'].sum(
                ).sort_values(ascending=False).head(10).index
                genre_segment_filtered = genre_segment[genre_segment['genre'].isin(
                    top_genres_list)]

                fig_genre_segment = px.bar(
                    genre_segment_filtered,
                    x='nominations',
                    y='genre',
                    color='segment',
                    orientation='h',
                    barmode='group',
                    color_discrete_map={'Indie': ACCENT, 'Non-Indie': PRIMARY},
                    title='🎭 Top 10 Genres: Nominations by Segment'
                )
                fig_genre_segment.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    legend=dict(orientation="h", yanchor="bottom",
                                y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_genre_segment, use_container_width=True)
            else:
                st.info("Could not process genre data.")
        else:
            st.info("No genre data available for awarded games.")

        st.markdown("---")

        # Top nominated games
        st.markdown("### 🌟 Most Nominated Games")
        top_nominated = df[df['total_nominations'] > 0].nlargest(20, 'total_nominations')[
            ['name', 'total_nominations', 'total_wins', 'is_indie', 'primary_genre']
        ].copy()
        top_nominated['segment'] = top_nominated['is_indie'].apply(
            lambda x: 'Indie' if x else 'Non-Indie')
        top_nominated = top_nominated.rename(columns={
            'name': 'Game',
            'total_nominations': 'Nominations',
            'total_wins': 'Wins',
            'segment': 'Type',
            'primary_genre': 'Genre'
        })
        top_nominated = top_nominated[[
            'Game', 'Type', 'Nominations', 'Wins', 'Genre']]
        st.dataframe(top_nominated, use_container_width=True, hide_index=True)
