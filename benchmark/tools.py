"""30 synthetic tools across 6 domains for benchmarking."""

from millwright.models import ToolDefinition


def get_tools() -> list[ToolDefinition]:
    return [
        # === File Operations (5) ===
        ToolDefinition(
            name="file_read",
            description="Read the contents of a file from the filesystem",
            category="file",
        ),
        ToolDefinition(
            name="file_write",
            description="Write content to a file on the filesystem",
            category="file",
        ),
        ToolDefinition(
            name="file_delete",
            description="Delete a file from the filesystem",
            category="file",
        ),
        ToolDefinition(
            name="file_list",
            description="List files and directories in a given path",
            category="file",
        ),
        ToolDefinition(
            name="file_copy",
            description="Copy a file from one location to another",
            category="file",
        ),

        # === HTTP (5) ===
        ToolDefinition(
            name="http_get",
            description="Make an HTTP GET request to a URL and return the response",
            category="http",
        ),
        ToolDefinition(
            name="http_post",
            description="Make an HTTP POST request with a JSON body to a URL",
            category="http",
        ),
        ToolDefinition(
            name="http_put",
            description="Make an HTTP PUT request to update a resource at a URL",
            category="http",
        ),
        ToolDefinition(
            name="http_delete",
            description="Make an HTTP DELETE request to remove a resource",
            category="http",
        ),
        ToolDefinition(
            name="http_download",
            description="Download a file from a URL and save it locally",
            category="http",
        ),

        # === Database (5) ===
        ToolDefinition(
            name="db_query",
            description="Execute a SQL query against the database and return results",
            category="database",
        ),
        ToolDefinition(
            name="db_insert",
            description="Insert a new row into a database table",
            category="database",
        ),
        ToolDefinition(
            name="db_update",
            description="Update existing rows in a database table",
            category="database",
        ),
        ToolDefinition(
            name="db_delete",
            description="Delete rows from a database table",
            category="database",
        ),
        ToolDefinition(
            name="db_schema",
            description="Get the schema definition of a database table",
            category="database",
        ),

        # === Text Processing (5) ===
        ToolDefinition(
            name="text_search",
            description="Search for a pattern or substring within text content",
            category="text",
        ),
        ToolDefinition(
            name="text_replace",
            description="Find and replace text patterns in a string",
            category="text",
        ),
        ToolDefinition(
            name="text_summarize",
            description="Generate a concise summary of a long text document",
            category="text",
        ),
        ToolDefinition(
            name="text_translate",
            description="Translate text from one language to another",
            category="text",
        ),
        ToolDefinition(
            name="text_extract",
            description="Extract structured data from unstructured text using patterns",
            category="text",
        ),

        # === Data Transform (5) ===
        ToolDefinition(
            name="json_parse",
            description="Parse a JSON string into a structured object",
            category="transform",
        ),
        ToolDefinition(
            name="csv_parse",
            description="Parse CSV data into rows and columns",
            category="transform",
        ),
        ToolDefinition(
            name="xml_parse",
            description="Parse XML document into a structured tree",
            category="transform",
        ),
        ToolDefinition(
            name="data_filter",
            description="Filter a dataset by applying conditions to fields",
            category="transform",
        ),
        ToolDefinition(
            name="data_aggregate",
            description="Aggregate data by grouping and computing statistics like sum, avg, count",
            category="transform",
        ),

        # === System (5) ===
        ToolDefinition(
            name="shell_exec",
            description="Execute a shell command and return its output",
            category="system",
        ),
        ToolDefinition(
            name="env_get",
            description="Get the value of an environment variable",
            category="system",
        ),
        ToolDefinition(
            name="process_list",
            description="List running processes on the system",
            category="system",
        ),
        ToolDefinition(
            name="log_write",
            description="Write a message to the application log",
            category="system",
        ),
        ToolDefinition(
            name="timer_set",
            description="Set a timer or schedule a task to run after a delay",
            category="system",
        ),
    ]
