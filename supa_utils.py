import streamlit as st
from supabase import create_client, Client


class SupaClient:
    def __init__(self):
        self.supa_url = st.secrets["supa_url"]
        self.supa_key = st.secrets["supa_key"]

        self.client: Client = create_client(self.supa_url, self.supa_key)

    def get(self, resource, eq_filter=None, is_filter=None, response_limit=1000):
        offset = 0
        all_records = []

        while True:
            if eq_filter is not None:
                result = self.client.table(resource).select('*') \
                    .eq(eq_filter[0], eq_filter[1]) \
                    .range(offset, offset + response_limit) \
                    .execute()
            elif is_filter is not None:
                result = self.client.table(resource).select('*') \
                    .filter(is_filter[0], 'is', is_filter[1]) \
                    .range(offset, offset + response_limit) \
                    .execute()
            else:
                result = self.client.table(resource).select('*') \
                    .range(offset, offset + response_limit) \
                    .execute()

            records = result.data
            all_records += records
            if len(records) < response_limit:
                break
            offset += response_limit

        return all_records
