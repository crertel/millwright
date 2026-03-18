"""120 benchmark queries with ground truth across 3 difficulty tiers.

Covers all 12 domains. Tier 3 queries are intentionally cross-domain and
ambiguous to stress the adaptive learning signal.
"""

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
        # Tier 1: Direct matches (45 queries)
        # ================================================================
        # -- file --
        BenchmarkQuery("read a file from disk", ["file_read"], 1, "file"),
        BenchmarkQuery("write data to a file", ["file_write"], 1, "file"),
        BenchmarkQuery("delete a file", ["file_delete"], 1, "file"),
        BenchmarkQuery("list directory contents", ["file_list"], 1, "file"),
        BenchmarkQuery("copy a file to another location", ["file_copy"], 1, "file"),
        BenchmarkQuery("move a file to a new path", ["file_move"], 1, "file"),
        BenchmarkQuery("compress a file with gzip", ["file_compress"], 1, "file"),
        # -- http --
        BenchmarkQuery("make an HTTP GET request", ["http_get"], 1, "http"),
        BenchmarkQuery("send a POST request with JSON body", ["http_post"], 1, "http"),
        BenchmarkQuery("download a file from a URL", ["http_download"], 1, "http"),
        BenchmarkQuery("open a WebSocket connection", ["http_websocket"], 1, "http"),
        # -- database --
        BenchmarkQuery("run a SQL query", ["db_query"], 1, "database"),
        BenchmarkQuery("insert a row into a database table", ["db_insert"], 1, "database"),
        BenchmarkQuery("update database records", ["db_update"], 1, "database"),
        BenchmarkQuery("delete rows from a table", ["db_delete"], 1, "database"),
        BenchmarkQuery("get the schema of a database table", ["db_schema"], 1, "database"),
        BenchmarkQuery("run a database migration", ["db_migrate"], 1, "database"),
        # -- text --
        BenchmarkQuery("search for a pattern in text", ["text_search"], 1, "text"),
        BenchmarkQuery("find and replace in a string", ["text_replace"], 1, "text"),
        BenchmarkQuery("summarize a long document", ["text_summarize"], 1, "text"),
        BenchmarkQuery("translate text to another language", ["text_translate"], 1, "text"),
        BenchmarkQuery("run a regex against text", ["text_regex"], 1, "text"),
        # -- transform --
        BenchmarkQuery("parse JSON data", ["json_parse"], 1, "transform"),
        BenchmarkQuery("parse a CSV file", ["csv_parse"], 1, "transform"),
        BenchmarkQuery("parse an XML document", ["xml_parse"], 1, "transform"),
        BenchmarkQuery("filter records by condition", ["data_filter"], 1, "transform"),
        BenchmarkQuery("sort data by a field", ["data_sort"], 1, "transform"),
        # -- system --
        BenchmarkQuery("execute a shell command", ["shell_exec"], 1, "system"),
        BenchmarkQuery("get an environment variable", ["env_get"], 1, "system"),
        BenchmarkQuery("list running processes", ["process_list"], 1, "system"),
        BenchmarkQuery("check disk usage", ["disk_usage"], 1, "system"),
        # -- auth --
        BenchmarkQuery("log in with username and password", ["auth_login"], 1, "auth"),
        BenchmarkQuery("create a JWT token", ["auth_token_create"], 1, "auth"),
        BenchmarkQuery("verify a TOTP code for MFA", ["auth_mfa_verify"], 1, "auth"),
        BenchmarkQuery("hash a password with bcrypt", ["auth_password_hash"], 1, "auth"),
        # -- crypto --
        BenchmarkQuery("encrypt data with AES", ["crypto_aes_encrypt", "crypto_encrypt"], 1, "crypto"),
        BenchmarkQuery("compute a SHA-256 hash", ["crypto_hash"], 1, "crypto"),
        BenchmarkQuery("generate an RSA key pair", ["crypto_keygen"], 1, "crypto"),
        BenchmarkQuery("sign data with a private key", ["crypto_sign"], 1, "crypto"),
        # -- messaging --
        BenchmarkQuery("send an email", ["msg_send_email"], 1, "messaging"),
        BenchmarkQuery("send a Slack message", ["msg_send_slack"], 1, "messaging"),
        BenchmarkQuery("push a message to a queue", ["msg_queue_push"], 1, "messaging"),
        # -- media --
        BenchmarkQuery("resize an image", ["media_resize_image"], 1, "media"),
        BenchmarkQuery("extract text from an image with OCR", ["media_ocr"], 1, "media"),
        BenchmarkQuery("generate a PDF from HTML", ["media_pdf_generate"], 1, "media"),

        # ================================================================
        # Tier 2: Indirect / rephrased matches (40 queries)
        # ================================================================
        # -- file --
        BenchmarkQuery(
            "check what's inside this document",
            ["file_read"], 2, "file",
        ),
        BenchmarkQuery(
            "save this content somewhere persistent",
            ["file_write"], 2, "file",
        ),
        BenchmarkQuery(
            "show me what's in this folder",
            ["file_list"], 2, "file",
        ),
        BenchmarkQuery(
            "make a backup copy of this file",
            ["file_copy"], 2, "file",
        ),
        BenchmarkQuery(
            "see the difference between these two versions",
            ["file_diff"], 2, "file",
        ),
        # -- http --
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
            "update just one field on the resource",
            ["http_patch"], 2, "http",
        ),
        BenchmarkQuery(
            "set up a real-time data stream from the server",
            ["http_stream", "http_websocket"], 2, "http",
        ),
        # -- database --
        BenchmarkQuery(
            "look up records matching a condition",
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
            "make the query faster by adding an index",
            ["db_index"], 2, "database",
        ),
        BenchmarkQuery(
            "show me the query execution plan",
            ["db_explain"], 2, "database",
        ),
        # -- text --
        BenchmarkQuery(
            "condense this long article into key points",
            ["text_summarize"], 2, "text",
        ),
        BenchmarkQuery(
            "convert this text to Spanish",
            ["text_translate"], 2, "text",
        ),
        BenchmarkQuery(
            "pull out the emails and phone numbers from this text",
            ["text_extract"], 2, "text",
        ),
        BenchmarkQuery(
            "is this text positive or negative in tone",
            ["text_sentiment"], 2, "text",
        ),
        # -- transform --
        BenchmarkQuery(
            "turn this JSON string into an object I can work with",
            ["json_parse"], 2, "transform",
        ),
        BenchmarkQuery(
            "reshape this data from rows to columns",
            ["data_pivot"], 2, "transform",
        ),
        BenchmarkQuery(
            "flatten the nested structure into a flat dict",
            ["data_flatten"], 2, "transform",
        ),
        # -- system --
        BenchmarkQuery(
            "run this command in the terminal",
            ["shell_exec"], 2, "system",
        ),
        BenchmarkQuery(
            "show me the running processes on the box",
            ["process_list"], 2, "system",
        ),
        BenchmarkQuery(
            "set up a recurring task on a schedule",
            ["cron_schedule"], 2, "system",
        ),
        BenchmarkQuery(
            "how much RAM is being used right now",
            ["memory_info"], 2, "system",
        ),
        # -- auth --
        BenchmarkQuery(
            "sign the user out and clear their session",
            ["auth_logout", "auth_session_destroy"], 2, "auth",
        ),
        BenchmarkQuery(
            "get a new access token using the refresh token",
            ["auth_token_refresh"], 2, "auth",
        ),
        BenchmarkQuery(
            "does this user have admin privileges",
            ["auth_role_check"], 2, "auth",
        ),
        # -- crypto --
        BenchmarkQuery(
            "make this data unreadable without the key",
            ["crypto_encrypt"], 2, "crypto",
        ),
        BenchmarkQuery(
            "validate the signature on this document",
            ["crypto_verify"], 2, "crypto",
        ),
        BenchmarkQuery(
            "generate a secure random identifier",
            ["crypto_random"], 2, "crypto",
        ),
        BenchmarkQuery(
            "create an SSL certificate for the domain",
            ["crypto_cert_create"], 2, "crypto",
        ),
        # -- messaging --
        BenchmarkQuery(
            "notify the team on Slack about the deployment",
            ["msg_send_slack"], 2, "messaging",
        ),
        BenchmarkQuery(
            "listen for events on this topic",
            ["msg_subscribe"], 2, "messaging",
        ),
        # -- media --
        BenchmarkQuery(
            "make this image smaller for the web",
            ["media_resize_image", "media_compress_image"], 2, "media",
        ),
        BenchmarkQuery(
            "read the text from this scanned document",
            ["media_ocr"], 2, "media",
        ),
        BenchmarkQuery(
            "transcribe this audio recording to text",
            ["media_transcribe_audio"], 2, "media",
        ),
        # -- monitoring --
        BenchmarkQuery(
            "check if the service is still up and responding",
            ["mon_healthcheck", "mon_uptime_check"], 2, "monitoring",
        ),
        BenchmarkQuery(
            "search the logs for errors in the last hour",
            ["mon_log_search"], 2, "monitoring",
        ),

        # ================================================================
        # Tier 3: Ambiguous / cross-domain queries (35 queries)
        # ================================================================
        BenchmarkQuery(
            "get the data",
            ["db_query", "http_get", "file_read", "cloud_storage_get"], 3, "database",
        ),
        BenchmarkQuery(
            "remove it",
            ["file_delete", "db_delete", "http_delete", "cloud_storage_delete"], 3, "file",
        ),
        BenchmarkQuery(
            "send the information",
            ["http_post", "msg_send_email", "msg_send_webhook", "msg_publish"], 3, "http",
        ),
        BenchmarkQuery(
            "process the input",
            ["json_parse", "csv_parse", "xml_parse", "yaml_parse", "text_extract"], 3, "transform",
        ),
        BenchmarkQuery(
            "store the results",
            ["file_write", "db_insert", "cloud_storage_put", "log_write"], 3, "file",
        ),
        BenchmarkQuery(
            "look something up",
            ["db_query", "text_search", "http_get", "cloud_dns_query", "mon_log_search"], 3, "database",
        ),
        BenchmarkQuery(
            "change the record",
            ["db_update", "text_replace", "file_write"], 3, "database",
        ),
        BenchmarkQuery(
            "convert the format",
            ["json_parse", "csv_parse", "xml_parse", "yaml_parse",
             "media_convert_format", "media_video_transcode"], 3, "transform",
        ),
        BenchmarkQuery(
            "clean up the data",
            ["data_filter", "text_replace", "db_delete", "db_vacuum", "db_truncate"], 3, "transform",
        ),
        BenchmarkQuery(
            "check the status",
            ["process_list", "http_get", "mon_healthcheck",
             "mon_uptime_check", "cloud_vm_list"], 3, "system",
        ),
        BenchmarkQuery(
            "make a copy",
            ["file_copy", "db_backup", "cloud_storage_get"], 3, "file",
        ),
        BenchmarkQuery(
            "analyze the content",
            ["text_summarize", "text_extract", "text_sentiment",
             "text_classify", "data_aggregate"], 3, "text",
        ),
        BenchmarkQuery(
            "find what I need",
            ["text_search", "db_query", "file_list", "mon_log_search"], 3, "text",
        ),
        BenchmarkQuery(
            "log the activity",
            ["log_write", "mon_audit_log", "mon_metric_push"], 3, "system",
        ),
        BenchmarkQuery(
            "aggregate the numbers",
            ["data_aggregate", "db_aggregate", "mon_metric_query"], 3, "transform",
        ),
        BenchmarkQuery(
            "secure the data",
            ["crypto_encrypt", "crypto_aes_encrypt", "auth_password_hash",
             "cloud_secret_set"], 3, "crypto",
        ),
        BenchmarkQuery(
            "authenticate the user",
            ["auth_login", "auth_oauth_flow", "auth_ldap_bind",
             "auth_api_key"], 3, "auth",
        ),
        BenchmarkQuery(
            "notify someone",
            ["msg_send_email", "msg_send_sms", "msg_send_slack",
             "msg_send_webhook", "msg_publish"], 3, "messaging",
        ),
        BenchmarkQuery(
            "deploy the code",
            ["cloud_function_deploy", "cloud_container_run", "shell_exec"], 3, "cloud",
        ),
        BenchmarkQuery(
            "back everything up",
            ["db_backup", "file_copy", "cloud_storage_put"], 3, "database",
        ),
        BenchmarkQuery(
            "verify the thing",
            ["crypto_verify", "crypto_jwt_verify", "crypto_cert_verify",
             "auth_password_verify", "auth_mfa_verify", "data_validate"], 3, "crypto",
        ),
        BenchmarkQuery(
            "schedule it for later",
            ["timer_set", "cron_schedule", "msg_schedule"], 3, "system",
        ),
        BenchmarkQuery(
            "encode the data",
            ["crypto_base64_encode", "text_encode", "json_stringify",
             "csv_write", "xml_write", "yaml_write"], 3, "transform",
        ),
        BenchmarkQuery(
            "show me the metrics",
            ["mon_metric_query", "mon_dashboard_create", "mon_report_generate",
             "mon_sla_check"], 3, "monitoring",
        ),
        BenchmarkQuery(
            "create a new instance",
            ["cloud_vm_create", "cloud_container_run", "auth_session_create",
             "db_seed"], 3, "cloud",
        ),
        BenchmarkQuery(
            "tear it down",
            ["cloud_vm_destroy", "db_truncate", "auth_session_destroy",
             "process_kill"], 3, "cloud",
        ),
        BenchmarkQuery(
            "handle the error",
            ["mon_incident_create", "msg_dead_letter", "msg_retry",
             "log_write", "mon_alert_create"], 3, "monitoring",
        ),
        BenchmarkQuery(
            "transform the image",
            ["media_resize_image", "media_crop_image", "media_convert_format",
             "media_compress_image", "media_watermark"], 3, "media",
        ),
        BenchmarkQuery(
            "extract the text",
            ["media_ocr", "media_pdf_extract", "text_extract",
             "media_transcribe_audio"], 3, "media",
        ),
        BenchmarkQuery(
            "generate a report",
            ["mon_report_generate", "media_pdf_generate",
             "data_aggregate", "text_template"], 3, "monitoring",
        ),
        BenchmarkQuery(
            "configure the routing",
            ["cloud_lb_configure", "cloud_dns_set", "http_proxy",
             "http_redirect"], 3, "cloud",
        ),
        BenchmarkQuery(
            "manage secrets",
            ["cloud_secret_get", "cloud_secret_set", "env_get",
             "crypto_keygen"], 3, "cloud",
        ),
        BenchmarkQuery(
            "broadcast the update",
            ["msg_broadcast", "msg_publish", "msg_batch_send",
             "msg_send_webhook"], 3, "messaging",
        ),
        BenchmarkQuery(
            "merge the data together",
            ["data_merge", "db_join", "file_merge"], 3, "transform",
        ),
        BenchmarkQuery(
            "validate the input",
            ["data_validate", "text_validate", "auth_mfa_verify",
             "crypto_cert_verify"], 3, "transform",
        ),
    ]
