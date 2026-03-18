"""200 synthetic tools across 12 domains for benchmarking.

Descriptions are intentionally messy — terse, verbose, jargon-heavy, informal,
or vague — to stress-test semantic search and reward adaptive learning.
"""

from millwright.models import ToolDefinition


def get_tools() -> list[ToolDefinition]:
    return [
        # =================================================================
        # File Operations (18 tools)
        # =================================================================
        ToolDefinition(
            name="file_read",
            description="Reads bytes or text from a local path. Returns contents as string or binary blob depending on mode flag.",
            category="file",
        ),
        ToolDefinition(
            name="file_write",
            description="Persist data to disk. Overwrites existing or creates new. Set append=True to add to end instead of clobbering.",
            category="file",
        ),
        ToolDefinition(
            name="file_delete",
            description="rm a file",
            category="file",
        ),
        ToolDefinition(
            name="file_list",
            description="Returns directory listing as array of entry objects with name, size, modified timestamp. Supports glob patterns for filtering.",
            category="file",
        ),
        ToolDefinition(
            name="file_copy",
            description="Duplicate a filesystem object from src to dst, preserving permissions and timestamps when possible",
            category="file",
        ),
        ToolDefinition(
            name="file_move",
            description="mv - relocate file or dir to new path",
            category="file",
        ),
        ToolDefinition(
            name="file_rename",
            description="Change the name of a file without moving it to a different directory. Just renames in place.",
            category="file",
        ),
        ToolDefinition(
            name="file_exists",
            description="Quick stat check — returns boolean for whether the given path points to an existing filesystem entry",
            category="file",
        ),
        ToolDefinition(
            name="file_info",
            description="Retrieve comprehensive metadata about a filesystem entry including size in bytes, creation time, last modified time, permissions bitmask, owner UID, group GID, inode number, and whether the entry is a regular file, directory, or symbolic link",
            category="file",
        ),
        ToolDefinition(
            name="file_watch",
            description="inotify wrapper - watch path for changes, fires callback on create/modify/delete events",
            category="file",
        ),
        ToolDefinition(
            name="file_lock",
            description="Advisory flock on a file descriptor for process-level mutual exclusion",
            category="file",
        ),
        ToolDefinition(
            name="file_chmod",
            description="Set POSIX permission bits. Takes octal like 0o755 or symbolic like u+rwx,go+rx.",
            category="file",
        ),
        ToolDefinition(
            name="file_compress",
            description="gzip/zstd/lz4 compression of file contents",
            category="file",
        ),
        ToolDefinition(
            name="file_decompress",
            description="Inflate a compressed file back to its original form. Supports gz, zst, lz4, bz2.",
            category="file",
        ),
        ToolDefinition(
            name="file_diff",
            description="Computes unified diff between two files, similar to GNU diff -u output",
            category="file",
        ),
        ToolDefinition(
            name="file_merge",
            description="Three-way merge of file contents using a common ancestor. Reports conflicts inline.",
            category="file",
        ),
        ToolDefinition(
            name="file_temp",
            description="mktemp — create a temporary file in the system temp directory, returns its path",
            category="file",
        ),
        ToolDefinition(
            name="file_checksum",
            description="Compute hash digest of file contents (md5, sha1, sha256, sha512)",
            category="file",
        ),

        # =================================================================
        # HTTP / Networking (18 tools)
        # =================================================================
        ToolDefinition(
            name="http_get",
            description="Fetch a resource. Sends GET and returns status + headers + body.",
            category="http",
        ),
        ToolDefinition(
            name="http_post",
            description="Submit data to a URL via HTTP POST. Default content-type application/json but supports form-encoded and multipart too.",
            category="http",
        ),
        ToolDefinition(
            name="http_put",
            description="Idempotent resource replacement per RFC 7231. Full entity body required.",
            category="http",
        ),
        ToolDefinition(
            name="http_delete",
            description="Send a DELETE request to remove the identified resource at the given URI",
            category="http",
        ),
        ToolDefinition(
            name="http_patch",
            description="Partial resource modification using JSON Merge Patch (RFC 7396) or JSON Patch (RFC 6902)",
            category="http",
        ),
        ToolDefinition(
            name="http_head",
            description="Like GET but response has no body — just returns headers. Good for checking if resource exists or getting content-length without downloading.",
            category="http",
        ),
        ToolDefinition(
            name="http_options",
            description="CORS preflight / capability discovery — returns Allow header with supported methods",
            category="http",
        ),
        ToolDefinition(
            name="http_download",
            description="Pull down a binary from a remote URL and write it to local storage. Supports resume on partial downloads.",
            category="http",
        ),
        ToolDefinition(
            name="http_upload",
            description="Push a local file up to a remote endpoint via multipart/form-data POST",
            category="http",
        ),
        ToolDefinition(
            name="http_stream",
            description="Server-sent events or chunked transfer-encoding consumer. Opens persistent connection and yields chunks.",
            category="http",
        ),
        ToolDefinition(
            name="http_websocket",
            description="Bidirectional real-time comms over WS/WSS protocol. Connect, send frames, receive frames.",
            category="http",
        ),
        ToolDefinition(
            name="http_graphql",
            description="Execute a GraphQL query or mutation against an endpoint. Handles variables and operation names.",
            category="http",
        ),
        ToolDefinition(
            name="http_soap",
            description="Legacy SOAP/XML web service call. Constructs envelope, sends to WSDL endpoint, parses response.",
            category="http",
        ),
        ToolDefinition(
            name="http_proxy",
            description="Forward a request through an intermediary proxy server. Supports HTTP and SOCKS5.",
            category="http",
        ),
        ToolDefinition(
            name="http_redirect",
            description="Follow or inspect redirect chains. Returns each hop with status code and location header.",
            category="http",
        ),
        ToolDefinition(
            name="http_cache",
            description="Manages a local HTTP response cache. Set TTL, invalidate entries, check freshness per Cache-Control headers.",
            category="http",
        ),
        ToolDefinition(
            name="http_retry",
            description="Wrapper that retries failed HTTP requests with exponential backoff and jitter. Configurable max attempts.",
            category="http",
        ),
        ToolDefinition(
            name="http_mock",
            description="Stub HTTP endpoints for testing — register URL patterns with canned responses, record incoming requests",
            category="http",
        ),

        # =================================================================
        # Database (18 tools)
        # =================================================================
        ToolDefinition(
            name="db_query",
            description="Run a SELECT or raw SQL and get result rows back",
            category="database",
        ),
        ToolDefinition(
            name="db_insert",
            description="INSERT INTO — adds one or more rows to a table. Returns generated IDs if any.",
            category="database",
        ),
        ToolDefinition(
            name="db_update",
            description="Modify existing rows matching a WHERE clause. Returns count of affected rows.",
            category="database",
        ),
        ToolDefinition(
            name="db_delete",
            description="DELETE FROM table WHERE ... — removes matching records permanently",
            category="database",
        ),
        ToolDefinition(
            name="db_schema",
            description="Introspect table DDL — returns column names, types, constraints, indexes, and foreign key relationships",
            category="database",
        ),
        ToolDefinition(
            name="db_migrate",
            description="Apply schema migration scripts in order. Tracks which migrations have been applied in a metadata table. Supports up and down.",
            category="database",
        ),
        ToolDefinition(
            name="db_backup",
            description="pg_dump / mysqldump style — snapshot entire database or specific tables to a dump file",
            category="database",
        ),
        ToolDefinition(
            name="db_restore",
            description="Load a database dump file to recreate schema and data. Reverse of backup.",
            category="database",
        ),
        ToolDefinition(
            name="db_index",
            description="CREATE INDEX — define a new index on one or more columns for faster lookups",
            category="database",
        ),
        ToolDefinition(
            name="db_transaction",
            description="BEGIN/COMMIT/ROLLBACK wrapper — execute multiple statements atomically within a transaction boundary",
            category="database",
        ),
        ToolDefinition(
            name="db_pool",
            description="Connection pool management — create, resize, drain, get stats on active/idle connections",
            category="database",
        ),
        ToolDefinition(
            name="db_replicate",
            description="Configure and manage read replicas. Streaming replication setup, lag monitoring, failover.",
            category="database",
        ),
        ToolDefinition(
            name="db_vacuum",
            description="Reclaim storage from dead tuples. Like VACUUM ANALYZE in PostgreSQL.",
            category="database",
        ),
        ToolDefinition(
            name="db_explain",
            description="EXPLAIN ANALYZE — show the query execution plan with actual timings and row estimates",
            category="database",
        ),
        ToolDefinition(
            name="db_seed",
            description="Populate tables with initial or test data from fixture files",
            category="database",
        ),
        ToolDefinition(
            name="db_truncate",
            description="TRUNCATE TABLE — fast delete of all rows, resets auto-increment. No WHERE clause, no row-level logging.",
            category="database",
        ),
        ToolDefinition(
            name="db_join",
            description="Execute a multi-table join query with configurable join types (INNER, LEFT, RIGHT, FULL OUTER) and return merged result set",
            category="database",
        ),
        ToolDefinition(
            name="db_aggregate",
            description="GROUP BY with aggregate funcs — COUNT, SUM, AVG, MIN, MAX, array_agg, etc.",
            category="database",
        ),

        # =================================================================
        # Text Processing (16 tools)
        # =================================================================
        ToolDefinition(
            name="text_search",
            description="Find occurrences of a substring or pattern in text, returns positions and context",
            category="text",
        ),
        ToolDefinition(
            name="text_replace",
            description="s/old/new/g — global find-and-replace in a string, supports regex capture groups",
            category="text",
        ),
        ToolDefinition(
            name="text_summarize",
            description="Takes a really long document and boils it down to the key points. Uses extractive or abstractive summarization depending on config.",
            category="text",
        ),
        ToolDefinition(
            name="text_translate",
            description="i18n text conversion between natural languages. Supports 100+ language pairs. Pass source and target locale codes.",
            category="text",
        ),
        ToolDefinition(
            name="text_extract",
            description="Pull structured fields out of unstructured text — dates, emails, phone numbers, addresses, named entities, etc.",
            category="text",
        ),
        ToolDefinition(
            name="text_tokenize",
            description="Break text into tokens/words/sentences. Multiple tokenizer backends: whitespace, BPE, SentencePiece, spaCy.",
            category="text",
        ),
        ToolDefinition(
            name="text_sentiment",
            description="Determines if text is positive, negative, or neutral. Returns score from -1.0 to 1.0 and label.",
            category="text",
        ),
        ToolDefinition(
            name="text_classify",
            description="Assign text to one or more categories from a predefined taxonomy. Zero-shot or fine-tuned classifier.",
            category="text",
        ),
        ToolDefinition(
            name="text_diff",
            description="Compare two strings and highlight insertions, deletions, and modifications at character or word level",
            category="text",
        ),
        ToolDefinition(
            name="text_template",
            description="Render a Jinja2/Mustache template with provided variable context. Returns the interpolated string.",
            category="text",
        ),
        ToolDefinition(
            name="text_regex",
            description="Compile and execute a regular expression against input text. Returns all match groups.",
            category="text",
        ),
        ToolDefinition(
            name="text_encode",
            description="Convert string between character encodings — UTF-8, Latin-1, Shift-JIS, etc.",
            category="text",
        ),
        ToolDefinition(
            name="text_decode",
            description="Decode bytes to string using specified encoding",
            category="text",
        ),
        ToolDefinition(
            name="text_validate",
            description="Check if text matches expected format — email, URL, phone, credit card, ISBN, etc.",
            category="text",
        ),
        ToolDefinition(
            name="text_highlight",
            description="Apply syntax highlighting or keyword highlighting to source code or text. Returns HTML/ANSI marked up output.",
            category="text",
        ),
        ToolDefinition(
            name="text_wordcount",
            description="Count words, characters, sentences, and paragraphs in text",
            category="text",
        ),

        # =================================================================
        # Data Transform (16 tools)
        # =================================================================
        ToolDefinition(
            name="json_parse",
            description="Deserialize a JSON string into native objects",
            category="transform",
        ),
        ToolDefinition(
            name="json_stringify",
            description="Serialize an object to JSON string. Options for pretty-printing, sorting keys, custom encoders.",
            category="transform",
        ),
        ToolDefinition(
            name="csv_parse",
            description="Read CSV/TSV data into list of dicts or list of lists. Handles quoting, custom delimiters, header row.",
            category="transform",
        ),
        ToolDefinition(
            name="csv_write",
            description="Serialize rows of data to CSV format string or file",
            category="transform",
        ),
        ToolDefinition(
            name="xml_parse",
            description="DOM/SAX parser for XML documents. Returns element tree or fires events.",
            category="transform",
        ),
        ToolDefinition(
            name="xml_write",
            description="Build an XML document from a dict/tree structure. Handles namespaces, CDATA, attributes.",
            category="transform",
        ),
        ToolDefinition(
            name="yaml_parse",
            description="Load YAML text into native data structures. Safe loader to prevent arbitrary code execution.",
            category="transform",
        ),
        ToolDefinition(
            name="yaml_write",
            description="Dump data structures to YAML formatted string",
            category="transform",
        ),
        ToolDefinition(
            name="data_filter",
            description="Filter rows/records that match given predicates. Like SQL WHERE but for in-memory data.",
            category="transform",
        ),
        ToolDefinition(
            name="data_aggregate",
            description="Group-by and reduce operations on tabular data — sum, mean, count, min, max per group",
            category="transform",
        ),
        ToolDefinition(
            name="data_sort",
            description="Sort records by one or more fields, ascending or descending. Stable sort.",
            category="transform",
        ),
        ToolDefinition(
            name="data_pivot",
            description="Reshape data from long to wide format (or vice versa). Like pandas pivot_table or melt.",
            category="transform",
        ),
        ToolDefinition(
            name="data_flatten",
            description="Flatten nested structures into a flat key-value representation. Nested keys joined with dots.",
            category="transform",
        ),
        ToolDefinition(
            name="data_merge",
            description="Join/merge two datasets on a common key. Inner, left, right, outer merge types.",
            category="transform",
        ),
        ToolDefinition(
            name="data_validate",
            description="Validate data against a JSON Schema or custom schema definition. Returns list of violations.",
            category="transform",
        ),
        ToolDefinition(
            name="data_sample",
            description="Random sampling from a dataset — simple random, stratified, or reservoir sampling",
            category="transform",
        ),

        # =================================================================
        # System Operations (16 tools)
        # =================================================================
        ToolDefinition(
            name="shell_exec",
            description="Run an arbitrary shell command. Returns stdout, stderr, and exit code. Timeout configurable.",
            category="system",
        ),
        ToolDefinition(
            name="env_get",
            description="Read an environment variable's value",
            category="system",
        ),
        ToolDefinition(
            name="env_set",
            description="Set or update an environment variable for the current process and children",
            category="system",
        ),
        ToolDefinition(
            name="process_list",
            description="ps aux equivalent — enumerate running processes with PID, CPU%, MEM%, command line",
            category="system",
        ),
        ToolDefinition(
            name="process_kill",
            description="Send a signal to a process. Default SIGTERM, can specify SIGKILL, SIGHUP, etc.",
            category="system",
        ),
        ToolDefinition(
            name="log_write",
            description="Append a structured log entry to the application log. Supports levels: DEBUG, INFO, WARN, ERROR, FATAL.",
            category="system",
        ),
        ToolDefinition(
            name="timer_set",
            description="Schedule something to happen after a delay. One-shot or repeating.",
            category="system",
        ),
        ToolDefinition(
            name="cron_schedule",
            description="Register a cron expression to run a task on a recurring schedule. Standard 5-field cron syntax.",
            category="system",
        ),
        ToolDefinition(
            name="disk_usage",
            description="df -h — report filesystem disk space usage for a given mount point or path",
            category="system",
        ),
        ToolDefinition(
            name="memory_info",
            description="Query system RAM — total, used, free, available, swap, cached, buffers",
            category="system",
        ),
        ToolDefinition(
            name="cpu_info",
            description="CPU details — model, cores, threads, current frequency, load average, per-core utilization",
            category="system",
        ),
        ToolDefinition(
            name="network_info",
            description="Enumerate network interfaces with IP addresses, MAC, MTU, rx/tx bytes and packets",
            category="system",
        ),
        ToolDefinition(
            name="hostname_get",
            description="Returns the system hostname and FQDN",
            category="system",
        ),
        ToolDefinition(
            name="uptime_get",
            description="How long the system has been running since last boot, plus load averages",
            category="system",
        ),
        ToolDefinition(
            name="signal_send",
            description="Deliver a POSIX signal to a process group or specific PID",
            category="system",
        ),
        ToolDefinition(
            name="sysctl_get",
            description="Read kernel tunables from /proc/sys or sysctl interface",
            category="system",
        ),

        # =================================================================
        # Authentication & Authorization (16 tools)
        # =================================================================
        ToolDefinition(
            name="auth_login",
            description="Authenticate a user with credentials (username+password, API key, etc.) and establish a session",
            category="auth",
        ),
        ToolDefinition(
            name="auth_logout",
            description="End user session, invalidate tokens, clean up server-side state",
            category="auth",
        ),
        ToolDefinition(
            name="auth_token_create",
            description="Mint a new bearer token — JWT, opaque, or reference token. Configurable claims, expiry, audience.",
            category="auth",
        ),
        ToolDefinition(
            name="auth_token_refresh",
            description="Exchange a refresh token for a new access token without re-authenticating",
            category="auth",
        ),
        ToolDefinition(
            name="auth_token_revoke",
            description="Invalidate a token so it can't be used anymore. Adds to denylist.",
            category="auth",
        ),
        ToolDefinition(
            name="auth_oauth_flow",
            description="Implements PKCE authorization code flow per OAuth 2.1 — handles redirect, code exchange, token receipt",
            category="auth",
        ),
        ToolDefinition(
            name="auth_api_key",
            description="Generate or validate an API key. Keys are scoped to specific operations and rate limits.",
            category="auth",
        ),
        ToolDefinition(
            name="auth_mfa_verify",
            description="Verify a second factor — TOTP code, SMS OTP, hardware key challenge-response, push notification approval",
            category="auth",
        ),
        ToolDefinition(
            name="auth_password_hash",
            description="Hash a password using bcrypt/argon2/scrypt with configurable work factor. Returns hash string.",
            category="auth",
        ),
        ToolDefinition(
            name="auth_password_verify",
            description="Check if a plaintext password matches a stored hash",
            category="auth",
        ),
        ToolDefinition(
            name="auth_session_create",
            description="Create a server-side session with configurable TTL and metadata. Returns session ID.",
            category="auth",
        ),
        ToolDefinition(
            name="auth_session_destroy",
            description="Kill a session by ID — removes from session store, cookie invalidation",
            category="auth",
        ),
        ToolDefinition(
            name="auth_role_check",
            description="Check whether a user/principal has a specific role. RBAC evaluation.",
            category="auth",
        ),
        ToolDefinition(
            name="auth_permission_grant",
            description="Add a permission to a role or user. Fine-grained access control management.",
            category="auth",
        ),
        ToolDefinition(
            name="auth_saml_assert",
            description="Validate a SAML assertion from an IdP. Checks signature, conditions, audience, expiry.",
            category="auth",
        ),
        ToolDefinition(
            name="auth_ldap_bind",
            description="Bind to an LDAP directory for authentication or search. Supports simple bind and SASL.",
            category="auth",
        ),

        # =================================================================
        # Cryptography (16 tools)
        # =================================================================
        ToolDefinition(
            name="crypto_encrypt",
            description="Encrypt plaintext using symmetric or asymmetric cipher. AES-GCM, ChaCha20-Poly1305, RSA-OAEP.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_decrypt",
            description="Reverse of encrypt — recover plaintext from ciphertext + key/nonce",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_sign",
            description="Produce a digital signature over data using a private key. Ed25519, ECDSA, RSA-PSS.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_verify",
            description="Verify a digital signature against data and a public key. Returns bool.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_hash",
            description="One-way hash function — SHA-256, SHA-3, BLAKE2, etc. Not for passwords (use bcrypt).",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_hmac",
            description="Keyed hash for message authentication. HMAC-SHA256, HMAC-SHA512.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_keygen",
            description="Generate cryptographic keys — symmetric (AES), asymmetric (RSA, EC), key exchange (X25519)",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_cert_create",
            description="Generate X.509 certificates — self-signed CA or leaf cert. Set subject, SANs, validity period.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_cert_verify",
            description="Validate an X.509 certificate chain against a trust store. Checks expiry, revocation, constraints.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_random",
            description="CSPRNG — generate cryptographically secure random bytes, integers, or UUIDs",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_base64_encode",
            description="base64 encode binary data to ASCII string. Standard or URL-safe alphabet.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_base64_decode",
            description="Decode a base64-encoded string back to raw bytes",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_aes_encrypt",
            description="AES specifically — block cipher encryption with CBC, CTR, or GCM mode. IV handling included.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_rsa_encrypt",
            description="RSA public-key encryption with OAEP or PKCS#1 v1.5 padding. Key sizes 2048-4096.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_jwt_sign",
            description="Create a signed JWT — set header, claims payload, sign with HS256/RS256/ES256. Returns compact serialization.",
            category="crypto",
        ),
        ToolDefinition(
            name="crypto_jwt_verify",
            description="Validate and decode a JWT — check signature, expiration, issuer, audience claims",
            category="crypto",
        ),

        # =================================================================
        # Messaging & Notifications (16 tools)
        # =================================================================
        ToolDefinition(
            name="msg_send_email",
            description="Dispatch an email via SMTP or API provider. To, CC, BCC, subject, HTML/text body, attachments.",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_send_sms",
            description="Send a text message to a phone number. Twilio/SNS backend.",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_send_slack",
            description="Post a message to a Slack channel or DM using the Slack Web API",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_send_webhook",
            description="Fire a webhook — HTTP POST to a registered callback URL with JSON payload",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_queue_push",
            description="Enqueue a message onto a message broker — SQS, RabbitMQ, Redis streams, Kafka produce",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_queue_pop",
            description="Dequeue/consume the next message from a queue. Supports visibility timeout and ack.",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_subscribe",
            description="Register a subscription to a topic or channel for push notifications",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_publish",
            description="Publish an event or message to a pub/sub topic. Fan-out to all subscribers.",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_broadcast",
            description="Blast a message to all connected clients or all members of a group simultaneously",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_template",
            description="Render a notification/email template with merge fields — handlebars/mustache syntax",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_schedule",
            description="Queue a message for future delivery at a specific timestamp. Delayed send.",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_retry",
            description="Re-attempt delivery of a failed message with backoff strategy",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_acknowledge",
            description="ACK a message to mark it as successfully processed so it's removed from the queue",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_dead_letter",
            description="Move a repeatedly-failed message to the dead letter queue for manual inspection",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_priority",
            description="Assign or change the priority level of a queued message (high/medium/low or numeric)",
            category="messaging",
        ),
        ToolDefinition(
            name="msg_batch_send",
            description="Send multiple messages in a single API call for throughput. Batch email, batch SMS, etc.",
            category="messaging",
        ),

        # =================================================================
        # Media Processing (16 tools)
        # =================================================================
        ToolDefinition(
            name="media_resize_image",
            description="Scale an image to new dimensions. Supports contain, cover, fill, and exact resize modes.",
            category="media",
        ),
        ToolDefinition(
            name="media_crop_image",
            description="Cut out a rectangular region from an image given x, y, width, height coordinates",
            category="media",
        ),
        ToolDefinition(
            name="media_convert_format",
            description="Transcode image between formats — PNG, JPEG, WebP, AVIF, TIFF, BMP, SVG rasterization",
            category="media",
        ),
        ToolDefinition(
            name="media_compress_image",
            description="Reduce image file size through lossy or lossless compression. Quality parameter 0-100.",
            category="media",
        ),
        ToolDefinition(
            name="media_extract_metadata",
            description="Read EXIF, IPTC, XMP metadata from image/video files — camera model, GPS coords, timestamps, etc.",
            category="media",
        ),
        ToolDefinition(
            name="media_generate_thumbnail",
            description="Create a small preview image from a larger source. Configurable max dimension.",
            category="media",
        ),
        ToolDefinition(
            name="media_watermark",
            description="Overlay a watermark (text or image) onto a target image at specified position and opacity",
            category="media",
        ),
        ToolDefinition(
            name="media_ocr",
            description="Optical character recognition — extract text content from images, scanned docs, screenshots",
            category="media",
        ),
        ToolDefinition(
            name="media_transcribe_audio",
            description="Speech-to-text — convert audio recording to transcript with timestamps. Whisper/Deepgram backend.",
            category="media",
        ),
        ToolDefinition(
            name="media_text_to_speech",
            description="TTS engine — synthesize natural-sounding audio from text input. Multiple voices and languages.",
            category="media",
        ),
        ToolDefinition(
            name="media_video_clip",
            description="Extract a segment from a video given start and end timestamps. No re-encoding if possible.",
            category="media",
        ),
        ToolDefinition(
            name="media_video_transcode",
            description="Convert video between codecs/containers — H.264, H.265, VP9, AV1 in MP4, MKV, WebM",
            category="media",
        ),
        ToolDefinition(
            name="media_pdf_generate",
            description="Create a PDF document from HTML, Markdown, or template data. Supports headers, footers, page numbers.",
            category="media",
        ),
        ToolDefinition(
            name="media_pdf_extract",
            description="Pull text, tables, and images out of PDF files. Page-by-page or full document.",
            category="media",
        ),
        ToolDefinition(
            name="media_screenshot",
            description="Capture a screenshot of a webpage or application window as PNG/JPEG",
            category="media",
        ),
        ToolDefinition(
            name="media_qr_generate",
            description="Generate QR code image from text, URL, or arbitrary data. Configurable size and error correction.",
            category="media",
        ),

        # =================================================================
        # Monitoring & Observability (17 tools)
        # =================================================================
        ToolDefinition(
            name="mon_metric_push",
            description="Emit a metric datapoint — counter increment, gauge value, histogram observation. StatsD/Prometheus push.",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_metric_query",
            description="Query time-series metrics — PromQL, Graphite, or custom DSL. Returns datapoints for a time range.",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_alert_create",
            description="Define an alert rule — condition expression, evaluation interval, notification channels, severity",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_alert_silence",
            description="Mute/snooze an alert for a specified duration or until manually unsilenced",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_healthcheck",
            description="Probe a service endpoint to determine if it's healthy. HTTP check, TCP check, or custom script.",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_trace_start",
            description="Begin a distributed trace span. Sets trace ID, span ID, parent span, service name, operation.",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_trace_end",
            description="Close an open trace span with status, duration, and optional error details",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_log_search",
            description="Full-text search across centralized logs — Elasticsearch/Loki/CloudWatch query syntax",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_log_tail",
            description="Live-stream log output from a service or log group. Like tail -f but for centralized logging.",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_dashboard_create",
            description="Create or update a monitoring dashboard with panels, queries, thresholds, and layout. Grafana-style.",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_incident_create",
            description="Open an incident record — severity, description, affected services, on-call assignment",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_incident_resolve",
            description="Close an incident with resolution summary, root cause, and timeline",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_sla_check",
            description="Evaluate whether a service is meeting its SLA targets — uptime percentage, latency p99, error rate",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_uptime_check",
            description="Periodic availability probe from multiple geographic locations. Reports latency and status.",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_anomaly_detect",
            description="Statistical anomaly detection on metric streams — z-score, MAD, or ML-based. Returns flagged intervals.",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_report_generate",
            description="Generate a periodic operations report — uptime summary, incident count, SLA compliance, top alerts",
            category="monitoring",
        ),
        ToolDefinition(
            name="mon_audit_log",
            description="Record an auditable event — who did what, when, from where. Immutable append-only log.",
            category="monitoring",
        ),

        # =================================================================
        # Cloud Infrastructure (17 tools)
        # =================================================================
        ToolDefinition(
            name="cloud_vm_create",
            description="Provision a new virtual machine instance — select image, size, region, network, SSH key",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_vm_destroy",
            description="Terminate and delete a cloud VM instance. Optionally preserves attached storage.",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_vm_list",
            description="Enumerate running cloud VM instances with status, IP, region, resource utilization",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_storage_put",
            description="Upload an object to cloud object storage (S3/GCS/Azure Blob). Set content-type, ACL, metadata.",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_storage_get",
            description="Download an object from cloud storage bucket. Supports range requests for partial reads.",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_storage_delete",
            description="Remove an object from cloud storage. Versioned buckets can soft-delete with a delete marker.",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_dns_set",
            description="Create or update a DNS record — A, AAAA, CNAME, MX, TXT, SRV. Set TTL.",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_dns_query",
            description="Look up DNS records for a domain. Returns all matching records of requested type.",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_lb_configure",
            description="Configure a load balancer — backends, health checks, routing rules, SSL termination",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_cdn_purge",
            description="Invalidate CDN cache for specific paths or patterns so fresh content is served",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_queue_create",
            description="Create a managed message queue (SQS, Cloud Tasks, etc.) with configurable retention and DLQ",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_function_deploy",
            description="Deploy a serverless function — upload code package, set runtime, memory, timeout, triggers",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_function_invoke",
            description="Trigger a cloud function synchronously or asynchronously with a JSON payload",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_container_run",
            description="Run a container image on managed infrastructure — ECS, Cloud Run, ACI. Set env vars, ports, scaling.",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_secret_get",
            description="Retrieve a secret value from a secrets manager — API keys, database passwords, certificates",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_secret_set",
            description="Store or rotate a secret in the secrets manager with versioning and access policy",
            category="cloud",
        ),
        ToolDefinition(
            name="cloud_iam_attach",
            description="Attach an IAM policy to a user, role, or service account. Grants specific cloud permissions.",
            category="cloud",
        ),
    ]
