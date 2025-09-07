
import streamlit as st
import pandas as pd
from rapidfuzz import process
import joblib
from pathlib import Path

# --- Utilities ---
def safe_get_book_field(book_row, field: str, default="N/A"):
    try:
        if book_row is None:
            return default
        val = book_row.get(field, default) if hasattr(book_row, "get") else getattr(book_row, field, default)
        return val if pd.notna(val) else default
    except Exception:
        return default

def get_best_match(query: str, choices, score_cutoff=75):
    if not query or not choices:
        return None
    return process.extractOne(query, choices, score_cutoff=score_cutoff)

# --- Load data ---
DATA_PATH = Path("data/Books.csv")
st.set_page_config(page_title="Books Explorer", layout="wide")

st.title("📚 Books Explorer (Streamlit)")

if not DATA_PATH.exists():
    st.error(f"Could not find {DATA_PATH}. Please place your Books.csv under a folder named 'data' next to this app.")
    st.stop()

BOOKS = pd.read_csv(DATA_PATH, dtype=str)
BOOKS.columns = [c.strip() for c in BOOKS.columns]

# Load precomputed index if available
INDEX_PATH = Path("book_index.joblib")
index = {}
if INDEX_PATH.exists():
    try:
        index = joblib.load(INDEX_PATH)
    except Exception as e:
        st.warning("Warning: Failed to load precomputed index. Recomputing on the fly.")
        index = {}

if not index:
    # build on the fly
    index["titles"] = BOOKS["title"].dropna().astype(str).unique().tolist() if "title" in BOOKS.columns else []
    index["authors"] = BOOKS["author"].dropna().astype(str).unique().tolist() if "author" in BOOKS.columns else []
    index["genres"] = BOOKS["genre"].dropna().astype(str).unique().tolist() if "genre" in BOOKS.columns else []

# --- Sidebar / Controls ---
action = st.sidebar.selectbox("Select action", [
    "Search by Title", "Search by Author", "Search by Genre", "Top Rated",
    "Recommend Random", "Show Thumbnail", "Pages", "Description", "Publisher", "Publish Date", "Average Rating"
])

query = st.sidebar.text_input("Query (title / author / genre)")
score_cutoff = st.sidebar.slider("Fuzzy score cutoff", 50, 100, 75)

# --- Actions ---
def show_book_row(book):
    st.write("**Title:**", safe_get_book_field(book, "title"))
    st.write("**Author:**", safe_get_book_field(book, "author"))
    st.write("**Genre:**", safe_get_book_field(book, "genre"))
    st.write("**Publisher:**", safe_get_book_field(book, "publisher"))
    st.write("**Published Date:**", safe_get_book_field(book, "published_date"))
    st.write("**Pages:**", safe_get_book_field(book, "pages"))
    st.write("**Average Rating:**", safe_get_book_field(book, "average_rating"))
    desc = safe_get_book_field(book, "description")
    if desc and desc != "N/A":
        st.write("**Description:**")
        st.write(desc)
    thumb = safe_get_book_field(book, "thumbnail")
    if thumb and str(thumb).startswith("http"):
        try:
            st.image(thumb, width=200)
        except Exception:
            st.write("Thumbnail URL present but failed to load image. URL:", thumb)

if action == "Search by Title":
    if not query:
        st.info("Type a book title in the sidebar 'Query' field.")
    else:
        match = get_best_match(query, index.get("titles", []), score_cutoff=score_cutoff)
        if match:
            matched_title = match[0]
            book = BOOKS.loc[BOOKS["title"].astype(str) == matched_title].iloc[0]
            st.success(f"Matched title: **{matched_title}** (score: {match[1]})")
            show_book_row(book)
        else:
            st.warning("No close title match found. Try lowering the cutoff. Showing a sample suggestion.")
            sample = BOOKS.sample(1).iloc[0]
            show_book_row(sample)

elif action == "Search by Author":
    if not query:
        st.info("Type an author name in the sidebar 'Query' field.")
    else:
        match = get_best_match(query, index.get("authors", []), score_cutoff=score_cutoff)
        if match:
            author = match[0]
            st.success(f"Matched author: **{author}** (score: {match[1]})")
            results = BOOKS[BOOKS["author"].astype(str) == author]
            st.write(f"Found {len(results)} books by {author}. Showing up to 10:")
            for _, row in results.head(10).iterrows():
                st.markdown(f"- **{safe_get_book_field(row, 'title')}** ({safe_get_book_field(row, 'published_date')})")
        else:
            st.warning("No close author match found. Try lowering the cutoff.")

elif action == "Search by Genre":
    if not query:
        st.info("Type a genre in the sidebar 'Query' field.")
    else:
        match = get_best_match(query, index.get("genres", []), score_cutoff=score_cutoff)
        if match:
            genre = match[0]
            st.success(f"Matched genre: **{genre}** (score: {match[1]})")
            results = BOOKS[BOOKS["genre"].astype(str).str.lower() == genre.lower()]
            if results.empty:
                st.warning("No books found for matched genre (case-insensitive exact). Trying contains() fallback.")
                results = BOOKS[BOOKS["genre"].astype(str).str.contains(genre, case=False, na=False)]
            st.write(f"Found {len(results)} books in genre '{genre}'. Showing up to 10:")
            for _, row in results.head(10).iterrows():
                st.markdown(f"- **{safe_get_book_field(row, 'title')}** by {safe_get_book_field(row, 'author')} ({safe_get_book_field(row, 'average_rating')}⭐)")
        else:
            st.warning("No close genre match found. Try lowering the cutoff.")

elif action == "Top Rated":
    if "average_rating" in BOOKS.columns:
        BOOKS["__rating_numeric__"] = pd.to_numeric(BOOKS["average_rating"], errors='coerce')
        top = BOOKS.nlargest(10, "__rating_numeric__").dropna(subset=["__rating_numeric__"]).head(10)
        st.write("🏆 Top Rated Books (by average_rating):")
        for i, (_, r) in enumerate(top.iterrows(), 1):
            st.markdown(f"{i}. **{safe_get_book_field(r,'title')}** by {safe_get_book_field(r,'author')} — ⭐ {safe_get_book_field(r,'average_rating')}")
        if "__rating_numeric__" in BOOKS.columns:
            BOOKS.drop(columns="__rating_numeric__", inplace=True)
    else:
        st.warning("No 'average_rating' column in dataset.")

elif action == "Recommend Random":
    sample = BOOKS.sample(1).iloc[0]
    st.write("Here's a random recommendation:")
    show_book_row(sample)

elif action == "Show Thumbnail":
    if not query:
        st.info("Type a book title in the sidebar 'Query' field to fetch its thumbnail.")
    else:
        match = get_best_match(query, index.get("titles", []), score_cutoff=score_cutoff)
        if match:
            matched_title = match[0]
            book = BOOKS.loc[BOOKS["title"].astype(str) == matched_title].iloc[0]
            thumb = safe_get_book_field(book, "thumbnail")
            if thumb and str(thumb).startswith("http"):
                st.image(thumb, width=300)
            else:
                st.warning("No valid thumbnail URL found for this book.")
        else:
            st.warning("No close title match found.")

elif action == "Pages":
    if not query:
        st.info("Type a book title in the sidebar 'Query' field.")
    else:
        match = get_best_match(query, index.get("titles", []), score_cutoff=score_cutoff)
        if match:
            book = BOOKS.loc[BOOKS["title"].astype(str) == match[0]].iloc[0]
            st.write(f"📄 **{safe_get_book_field(book,'title')}** — {safe_get_book_field(book,'pages')} pages")
        else:
            st.warning("No close title match found.")

elif action == "Description":
    if not query:
        st.info("Type a book title in the sidebar 'Query' field.")
    else:
        match = get_best_match(query, index.get("titles", []), score_cutoff=score_cutoff)
        if match:
            book = BOOKS.loc[BOOKS["title"].astype(str) == match[0]].iloc[0]
            st.write(f"📝 Description of **{safe_get_book_field(book,'title')}**:")
            st.write(safe_get_book_field(book, "description"))
        else:
            st.warning("No close title match found.")

elif action == "Publisher":
    if not query:
        st.info("Type a book title in the sidebar 'Query' field.")
    else:
        match = get_best_match(query, index.get("titles", []), score_cutoff=score_cutoff)
        if match:
            book = BOOKS.loc[BOOKS["title"].astype(str) == match[0]].iloc[0]
            st.write(f"🏢 Publisher for **{safe_get_book_field(book,'title')}**: {safe_get_book_field(book,'publisher')}")
        else:
            st.warning("No close title match found.")

elif action == "Publish Date":
    if not query:
        st.info("Type a book title in the sidebar 'Query' field.")
    else:
        match = get_best_match(query, index.get("titles", []), score_cutoff=score_cutoff)
        if match:
            book = BOOKS.loc[BOOKS["title"].astype(str) == match[0]].iloc[0]
            st.write(f"📅 Publish date for **{safe_get_book_field(book,'title')}**: {safe_get_book_field(book,'published_date')}")
        else:
            st.warning("No close title match found.")

elif action == "Average Rating":
    if not query:
        st.info("Type a book title in the sidebar 'Query' field.")
    else:
        match = get_best_match(query, index.get("titles", []), score_cutoff=score_cutoff)
        if match:
            book = BOOKS.loc[BOOKS["title"].astype(str) == match[0]].iloc[0]
            st.write(f"⭐ Average rating for **{safe_get_book_field(book,'title')}**: {safe_get_book_field(book,'average_rating')}")
        else:
            st.warning("No close title match found.")
