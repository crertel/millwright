"""50 benchmark queries with ground truth across 3 difficulty tiers."""

from dataclasses import dataclass


@dataclass
class BenchmarkQuery:
    query: str
    expected_tools: list[str]  # acceptable correct tools
    tier: int  # 1=direct, 2=indirect, 3=ambiguous
    category: str  # primary category for feedback simulation


def get_queries() -> list[BenchmarkQuery]:
    return [
        # ================================================================
        # Tier 1: Direct matches (20 queries)
        # ================================================================
        BenchmarkQuery("read a file", ["file_read"], 1, "file"),
        BenchmarkQuery("write data to a file", ["file_write"], 1, "file"),
        BenchmarkQuery("delete a file", ["file_delete"], 1, "file"),
        BenchmarkQuery("list directory contents", ["file_list"], 1, "file"),
        BenchmarkQuery("copy a file", ["file_copy"], 1, "file"),
        BenchmarkQuery("make a GET request", ["http_get"], 1, "http"),
        BenchmarkQuery("send a POST request with JSON", ["http_post"], 1, "http"),
        BenchmarkQuery("update a resource via HTTP PUT", ["http_put"], 1, "http"),
        BenchmarkQuery("delete an HTTP resource", ["http_delete"], 1, "http"),
        BenchmarkQuery("download a file from a URL", ["http_download"], 1, "http"),
        BenchmarkQuery("run a SQL query", ["db_query"], 1, "database"),
        BenchmarkQuery("insert a row into the database", ["db_insert"], 1, "database"),
        BenchmarkQuery("update database records", ["db_update"], 1, "database"),
        BenchmarkQuery("delete rows from a table", ["db_delete"], 1, "database"),
        BenchmarkQuery("get table schema", ["db_schema"], 1, "database"),
        BenchmarkQuery("search for text", ["text_search"], 1, "text"),
        BenchmarkQuery("find and replace in text", ["text_replace"], 1, "text"),
        BenchmarkQuery("parse JSON data", ["json_parse"], 1, "transform"),
        BenchmarkQuery("execute a shell command", ["shell_exec"], 1, "system"),
        BenchmarkQuery("get an environment variable", ["env_get"], 1, "system"),

        # ================================================================
        # Tier 2: Indirect / rephrased matches (15 queries)
        # ================================================================
        BenchmarkQuery(
            "check what's inside this document",
            ["file_read"], 2, "file",
        ),
        BenchmarkQuery(
            "save this content somewhere",
            ["file_write"], 2, "file",
        ),
        BenchmarkQuery(
            "remove this file I don't need anymore",
            ["file_delete"], 2, "file",
        ),
        BenchmarkQuery(
            "show me what's in this folder",
            ["file_list"], 2, "file",
        ),
        BenchmarkQuery(
            "fetch a webpage",
            ["http_get"], 2, "http",
        ),
        BenchmarkQuery(
            "submit form data to the server",
            ["http_post"], 2, "http",
        ),
        BenchmarkQuery(
            "grab that file from the internet",
            ["http_download"], 2, "http",
        ),
        BenchmarkQuery(
            "look up records in the database",
            ["db_query"], 2, "database",
        ),
        BenchmarkQuery(
            "add a new entry to the table",
            ["db_insert"], 2, "database",
        ),
        BenchmarkQuery(
            "what columns does this table have",
            ["db_schema"], 2, "database",
        ),
        BenchmarkQuery(
            "condense this long article",
            ["text_summarize"], 2, "text",
        ),
        BenchmarkQuery(
            "convert this text to Spanish",
            ["text_translate"], 2, "text",
        ),
        BenchmarkQuery(
            "pull out the key fields from this text",
            ["text_extract"], 2, "text",
        ),
        BenchmarkQuery(
            "run this command in the terminal",
            ["shell_exec"], 2, "system",
        ),
        BenchmarkQuery(
            "show me the running processes",
            ["process_list"], 2, "system",
        ),

        # ================================================================
        # Tier 3: Ambiguous queries (15 queries)
        # ================================================================
        BenchmarkQuery(
            "get the data",
            ["db_query", "http_get", "file_read"], 3, "database",
        ),
        BenchmarkQuery(
            "remove it",
            ["file_delete", "db_delete", "http_delete"], 3, "file",
        ),
        BenchmarkQuery(
            "send the information",
            ["http_post", "http_put", "log_write"], 3, "http",
        ),
        BenchmarkQuery(
            "process the input",
            ["json_parse", "csv_parse", "xml_parse", "text_extract"], 3, "transform",
        ),
        BenchmarkQuery(
            "store the results",
            ["file_write", "db_insert", "log_write"], 3, "file",
        ),
        BenchmarkQuery(
            "look something up",
            ["db_query", "text_search", "http_get"], 3, "database",
        ),
        BenchmarkQuery(
            "change the record",
            ["db_update", "text_replace", "file_write"], 3, "database",
        ),
        BenchmarkQuery(
            "convert the format",
            ["json_parse", "csv_parse", "xml_parse"], 3, "transform",
        ),
        BenchmarkQuery(
            "clean up the data",
            ["data_filter", "text_replace", "db_delete"], 3, "transform",
        ),
        BenchmarkQuery(
            "check the status",
            ["process_list", "http_get", "env_get"], 3, "system",
        ),
        BenchmarkQuery(
            "make a copy",
            ["file_copy", "db_insert", "file_write"], 3, "file",
        ),
        BenchmarkQuery(
            "analyze the content",
            ["text_summarize", "text_extract", "data_aggregate"], 3, "text",
        ),
        BenchmarkQuery(
            "find what I need",
            ["text_search", "db_query", "file_list"], 3, "text",
        ),
        BenchmarkQuery(
            "log the activity",
            ["log_write", "file_write", "db_insert"], 3, "system",
        ),
        BenchmarkQuery(
            "aggregate the numbers",
            ["data_aggregate", "db_query", "data_filter"], 3, "transform",
        ),
    ]
