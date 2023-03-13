from datetime import datetime

import streamlit as st
import requests
import pandas as pd
from typing import List
from models.tracks import TrackOut
from models.user import UserCreate
import altair as alt

# Endpoint URLs
USERS_URL = "http://localhost:8000/users"
TRACKS_URL = "http://localhost:8000/tracks"
USER_TRACKS_URL = "http://localhost:8000/users/{}/tracks"
ARTIST_TRACKS_URL = "http://localhost:8000/tracks/artists/{}"
RECOMENDATIONS_URL = "http://localhost:8000/recomendation/all_tracks/{}"

# Streamlit app
st.set_page_config(page_title="Music Recommendation App")


# Define helper functions
def get_all_users() -> List[str]:
    response = requests.get(USERS_URL)
    users = response.json()
    return [user["user_id"] for user in users]


def get_user_recomended_artist(user_id: str):
    response = requests.get(RECOMENDATIONS_URL.format(user_id))
    artists = response.json()
    df = pd.DataFrame.from_dict(artists)
    return df


def create_user(user: UserCreate) -> str:
    response = requests.post(USERS_URL, json=user.dict())
    user_id = response.json()["user_id"]
    return user_id


def create_track(track: TrackOut) -> str:
    response = requests.post(TRACKS_URL, json=track.dict())
    track_id = response.json()["trackid"]
    return track_id


# Define Streamlit pages
def main_page():
    # Display a list of all users
    users = get_all_users()
    selected_user = st.selectbox("Select a user", users)

    # Display the top 10 recommended artist for the selected user
    user_artists = get_user_recomended_artist(selected_user)
    print(user_artists)
    st.write("Top 10 Recommended Artist:")
    st.table(user_artists.head(10))

    # Create a bar chart of the recommended artists
    chart = alt.Chart(user_artists.head(50)).mark_bar().encode(
        x=alt.X('estimation:Q', axis=alt.Axis(title='Estimation')),
        y=alt.Y('artist:N', sort='-x', axis=alt.Axis(title='Artist'))
    ).properties(height=500)
    st.altair_chart(chart, use_container_width=True)


def create_user_page():
    st.title("Add User")
    # Display a form to create a new user
    st.write("Create a new user:")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.slider("Age", 18, 100, 20)
    country = st.text_input("Country")
    password = st.text_input("Password", type="password")

    if st.button("Create User"):
        new_user = UserCreate(gender=gender, age=age, country=country, password=password)
        user_id = create_user(new_user)
        st.success(f"New user created with ID: {user_id}")


def add_track_page():
    st.title("Add Track to User")

    # Get list of all users
    users = requests.get("http://localhost:8000/users").json()
    user_ids = [user["user_id"] for user in users]

    # Select user to add track to
    selected_user = st.selectbox("Select User", user_ids)

    # Get user's current tracks
    user_tracks = requests.get(f"http://localhost:8000/users/{selected_user}/tracks").json()
    current_tracks = [track["trackname"] for track in user_tracks]

    # Get all tracks
    all_tracks = pd.DataFrame(requests.get("http://localhost:8000/tracks").json())
    all_tracks = all_tracks[['trackid', 'trackname', 'artid', 'artname']]

    # Input new track information
    st.header("Add New Track")
    track_name = st.selectbox("Track Name", all_tracks['trackname'].unique())

    # Get the artid and trackid from the all_tracks DataFrame
    trackid = all_tracks.loc[all_tracks['trackname'] == track_name, 'trackid'].iloc[0]
    artist_name = all_tracks.loc[all_tracks['trackid'] == trackid, 'artname'].iloc[0]
    artid = all_tracks.loc[all_tracks['trackid'] == trackid, 'artid'].iloc[0]


    # Add track to user
    if st.button("Add Track"):
        track = {
            "user_id": selected_user,
            "timestamp": str(datetime.now()),
            "artid": artid,
            "artname": artist_name,
            "trackid": trackid,
            "trackname": track_name
        }
        response = requests.post("http://localhost:8000/tracks", json=track)
        if response.status_code == 200:
            st.success(f"Added track '{track_name}' by '{artist_name}' to user '{selected_user}'")
            st.info("Refresh the page to see the updated list of user tracks")
        else:
            st.error("Failed to add track to user")

    # Show current tracks for user
    st.header("Current Tracks")
    for track in current_tracks:
        st.write(track)


def main():
    # Define Streamlit pages
    pages = {
        "Main": main_page,
        "Create User": create_user_page,
        "Add Track": add_track_page
    }

    # Create a Streamlit app with page navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", tuple(pages.keys()))
    pages[page]()


if __name__ == '__main__':
    main()
