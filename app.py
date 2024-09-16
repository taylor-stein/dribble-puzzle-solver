import streamlit as st
import pandas as pd
from supa_utils import SupaClient

supa_client = SupaClient()
img_base_url = 'https://ekcvtfaavlzpyfxixazo.supabase.co/storage/v1/object/public/headshots/'


@st.cache_data
def load_player_data():
    players = supa_client.get('players')
    df = pd.DataFrame(players)
    df.sort_values(by='name', inplace=True)
    df.set_index('id', inplace=True, drop=True)
    return df


@st.cache_data
def get_player_teammates(player_id):
    player_teammates = supa_client.get(
        resource='teammates_season_details',
        eq_filter=('player_a', player_id)
    )
    player_teammates_df = pd.DataFrame(player_teammates)
    return player_teammates_df


def insert_user_puzzle(username, start_player_id, end_player_id, solution_player_id):
    response = supa_client.client.table('user_puzzles').insert([
        {
            'username': username,
            'start_player_id': start_player_id,
            'end_player_id': end_player_id,
            'solution_player_id': solution_player_id
        }
    ]).execute()

def delete_user_puzzle(user_puzzle_id):
    response = supa_client.client.table('user_puzzles').delete().eq("id", user_puzzle_id).execute()


def show_username():
    col1, spacer = st.columns([0.2, 0.8])
    with col1:
        username = st.text_input(
            label='Puzzle Creator ID:'
        )

        st.session_state.username = username


def get_my_puzzles():
    my_puzzles = supa_client.get(
        resource='user_puzzle_details',
        eq_filter=('username', st.session_state.username.upper())
    )
    return pd.DataFrame(my_puzzles)


def submit_button(is_disabled):
    clicked = st.button(
        label='Submit Puzzle',
        on_click=lambda: insert_user_puzzle(
            username=st.session_state.username.upper(),
            start_player_id=int(st.session_state.start_player_id),
            end_player_id=int(st.session_state.end_player_id),
            solution_player_id=int(st.session_state.solution_player_id)
        ),
        disabled=is_disabled
    )


def get_random_puzzle(players_df):
    filtered_players_df = players_df[players_df.search_rank > 200].copy()
    sample_players_df = filtered_players_df.sample(2)
    st.session_state.start_player_id = sample_players_df.index.tolist()[0]
    st.session_state.end_player_id = sample_players_df.index.tolist()[1]


def get_headshot_url(player_id, has_headshot, size='large'):
    size_map = {
        'large': '',
        'medium': '_medium',
        'small': '_small'
    }

    if has_headshot:
        return f"{img_base_url}{player_id}{size_map[size]}.png"
    else:
        return f"{img_base_url}default.png"


def show_solution_player(players_df, player_id):
    player = players_df.loc[player_id]
    player_col_1, player_col_2 = st.columns(spec=(0.1, 0.9), gap='small')

    with player_col_1:
        if player.has_headshot:
            player_img_url = f"{img_base_url}{player_id}_medium.png"
        else:
            player_img_url = f"{img_base_url}default.png"
        st.image(player_img_url, width=50)

    with player_col_2:
        st.markdown(f"""
                    <p style="display: flex; align-items: center; margin: 0px; line-height: 40px;">
                    {player.display_name}
                    </p>
                    """,
                    unsafe_allow_html=True)


def show_my_puzzles():
    puzzles_df = get_my_puzzles()
    if len(puzzles_df) == 0:
        return

    st.markdown(
        f"""
        <h3>Puzzles Found: {len(puzzles_df)}</h3>
        """,
        unsafe_allow_html=True
    )

    player_names = ['start', 'end', 'solution']
    for name in player_names:
        puzzles_df[f"{name}_player_name"] = puzzles_df[f"{name}_player"].apply(lambda x: x.get('display_name'))
        puzzles_df[f"{name}_player_headshot_url"] = puzzles_df[f"{name}_player"].apply(
            lambda x: get_headshot_url(x.get('id'), x.get('has_headshot'))
        )

    my_puzzles_df = st.dataframe(
        data=puzzles_df[[
            'id',
            'created_at',
            'start_player_headshot_url',
            'start_player_name',
            'end_player_headshot_url',
            'end_player_name',
            'solution_player_headshot_url',
            'solution_player_name'
        ]],
        column_config={
            'id': None,
            'created_at': st.column_config.DateColumn(),
            'start_player_headshot_url': st.column_config.ImageColumn(width='small', label=''),
            'start_player_name': st.column_config.TextColumn(label='Start Player'),
            'end_player_headshot_url': st.column_config.ImageColumn(width='small', label=''),
            'end_player_name': st.column_config.TextColumn(label='End Player'),
            'solution_player_headshot_url': st.column_config.ImageColumn(width='small', label=''),
            'solution_player_name': st.column_config.TextColumn(label='Solution Player'),
        },
        hide_index=True,
        selection_mode='single-row',
        on_select='rerun'
    )

    if len(my_puzzles_df['selection']['rows']) > 0:
        st.session_state.delete_my_puzzle_disabled = False
        selected_user_puzzle_id = puzzles_df.iloc[my_puzzles_df['selection']['rows'][0]].id
        st.session_state.selected_user_puzzle_id = selected_user_puzzle_id
    else:
        st.session_state.delete_my_puzzle_disabled = None

    if st.session_state.delete_my_puzzle_disabled is None:
        delete_button_disabled = True
    else:
        delete_button_disabled = False

    delete_button = st.button(
        label='🗑️ Delete',
        on_click=lambda: delete_user_puzzle(user_puzzle_id=st.session_state.selected_user_puzzle_id),
        disabled=delete_button_disabled
    )


def main():
    st.set_page_config(
        page_title='DribbleGame Puzzle Creator',
        page_icon='🏀',
        layout='wide'
    )

    st.title('DribbleGame Puzzle Creator Tool')
    for k in [
        'start_player_id',
        'end_player_id',
        'solution_player_id',
        'solution_players_df',
        'username',
        'delete_my_puzzle_disabled',
        'selected_user_puzzle_id',
    ]:
        if k not in st.session_state:
            st.session_state[k] = None

    players_df = load_player_data()
    show_username()

    tab1, tab2 = st.tabs(['Puzzle Creator', 'My Puzzles'])
    with tab1:
        st.markdown("<h3>Customize your puzzle</h3>", unsafe_allow_html=True)
        st.button(label='Randomize', on_click=lambda: get_random_puzzle(players_df))

        col1, col2, spacer = st.columns([0.25, 0.25, 0.5], gap='small')

        with col1:
            st.session_state.start_player_id = st.selectbox(
                label='Select a Start Player',
                options=players_df.index.tolist(),
                format_func=lambda x: players_df.loc[x].display_name,
                index=players_df.index.tolist().index(st.session_state.start_player_id) if st.session_state.start_player_id else None
            )

            if st.session_state.start_player_id:
                player_img_url = get_headshot_url(
                    player_id=st.session_state.start_player_id,
                    has_headshot=players_df.loc[st.session_state.start_player_id].has_headshot
                )

                st.image(
                    image=player_img_url,
                    use_column_width='auto'
                )

        with col2:
            st.session_state.end_player_id = st.selectbox(
                label='Select an End Player',
                options=players_df.index.tolist(),
                format_func=lambda x: players_df.loc[x].display_name,
                index=players_df.index.tolist().index(st.session_state.end_player_id) if st.session_state.end_player_id else None
            )

            if st.session_state.end_player_id:
                player_img_url = get_headshot_url(
                    player_id=st.session_state.end_player_id,
                    has_headshot=players_df.loc[st.session_state.end_player_id].has_headshot
                )

                st.image(
                    image=player_img_url,
                    use_column_width='auto'
                )

        if st.session_state.start_player_id:
            start_player_teammates = get_player_teammates(st.session_state.start_player_id).player_b.tolist()

        if st.session_state.end_player_id:
            end_player_teammates = get_player_teammates(st.session_state.end_player_id).player_b.tolist()

        if st.session_state.start_player_id and st.session_state.end_player_id:
            solution_player_ids = [p_id for p_id in start_player_teammates if p_id in end_player_teammates]
            st.session_state.solution_players_df = players_df.loc[solution_player_ids]
            st.session_state.solution_players_df.sort_values(by='search_rank', ascending=False, inplace=True)
            st.markdown(f"<h3>One-Shot Solutions ({len(st.session_state.solution_players_df)})</h3> ",
                        unsafe_allow_html=True)

        if st.session_state.solution_players_df is not None:
            if len(st.session_state.solution_players_df) > 0:

                start_player_last_name = players_df.loc[st.session_state.start_player_id].last_name
                end_player_last_name = players_df.loc[st.session_state.end_player_id].last_name

                start_connections_df = st.session_state.solution_players_df.merge(
                    get_player_teammates(st.session_state.start_player_id),
                    how='inner',
                    left_index=True,
                    right_on='player_b'
                )

                start_connections_df.set_index('player_b', drop=True, inplace=True)
                start_connections_df.rename(
                    columns={
                        'last_season_teammates': 'last_season_with_start',
                        'seasons_teammates': 'seasons_with_start',
                        'years_teammates': 'years_teammates_start'
                    },
                    inplace=True
                )

                end_connections_df = st.session_state.solution_players_df.merge(
                    get_player_teammates(st.session_state.end_player_id),
                    how='inner',
                    left_index=True,
                    right_on='player_b'
                )

                end_connections_df.set_index('player_b', drop=True, inplace=True)

                end_connections_df.rename(
                    columns={
                        'last_season_teammates': 'last_season_with_end',
                        'seasons_teammates': 'seasons_with_end',
                        'years_teammates': 'years_teammates_end'
                    },
                    inplace=True
                )

                viz_df = st.session_state.solution_players_df.copy()
                viz_df = viz_df.merge(
                    start_connections_df[['last_season_with_start', 'seasons_with_start', 'years_teammates_start']],
                    how='inner',
                    left_index=True,
                    right_index=True
                )

                viz_df = viz_df.merge(
                    end_connections_df[['last_season_with_end', 'seasons_with_end', 'years_teammates_end']],
                    how='inner',
                    left_index=True,
                    right_index=True
                )

                viz_df['total_shared_seasons'] = viz_df['years_teammates_start'] + viz_df['years_teammates_end']

                viz_df['headshot_url'] = viz_df.apply(
                    lambda p: get_headshot_url(p.name, p.has_headshot, size='medium'),
                    axis=1
                )

                one_shot_df = st.dataframe(
                    data=viz_df[[
                        'headshot_url',
                        'display_name',
                        'search_rank',
                        'total_shared_seasons',
                        'seasons_with_start',
                        'seasons_with_end'
                    ]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'headshot_url': st.column_config.ImageColumn(width='small', label=''),
                        'display_name': st.column_config.TextColumn(label='Name'),
                        'search_rank': st.column_config.ProgressColumn(label='Notoriety', min_value=0, max_value=745, format="%d"),
                        'seasons_with_start': st.column_config.ListColumn(label=f'Seasons w/ {start_player_last_name}'),
                        'seasons_with_end': st.column_config.ListColumn(label=f'Seasons w/ {end_player_last_name}')
                    },
                    selection_mode='single-row',
                    on_select='rerun'
                )
                if len(one_shot_df['selection']['rows']) > 0:
                    st.session_state.solution_player_id = st.session_state.solution_players_df.iloc[one_shot_df['selection']['rows'][0]].name
                else:
                    st.session_state.solution_player_id = None

        submit_is_disabled = (st.session_state.solution_player_id is None) or (len(st.session_state.username) == 0)
        submit_button(submit_is_disabled)

    with tab2:
        show_my_puzzles()


if __name__ == "__main__":
    main()
