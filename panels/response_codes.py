import os
from datetime import datetime, timedelta

import polars as pl
from dotenv import load_dotenv
from logfire.query_client import AsyncLogfireQueryClient

load_dotenv()


async def get_reponse_codes_table(
    min_datetime: datetime, max_datetime: datetime, user_email: str
):
    query = f"""
select
    url_path,
    http_response_status_code as response_code,
    count(*) as num_seen
from records
WHERE
  (
    span_name LIKE 'GET%' OR span_name LIKE 'POST%'
  )
    and url_path != '/health' and url_path like '/v%' 
    AND attributes ->> 'http.request.header.x_user_email' ->> 0 = '{user_email}'
group by url_path, http_response_status_code
order by num_seen desc
    """

    async with AsyncLogfireQueryClient(
        read_token=os.environ.get("LOGFIRE_API_KEY", "")
    ) as client:
        df_from_arrow = pl.from_arrow(
            await client.query_arrow(
                sql=query, min_timestamp=min_datetime, max_timestamp=max_datetime
            )
        )
        df = df_from_arrow.to_pandas()
        return df


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        get_reponse_codes_table(
            min_datetime=datetime.today() - timedelta(days=14),
            max_datetime=datetime.today(),
            user_email="aidar@compasslabs.ai",
        )
    )
