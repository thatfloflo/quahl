# Quahl IPC and JSON-RPC Interface Description

## Introduction

Quahl offers Inter-Process Communication via TCP socket.

To activate the IPC capabilities, launch Quahl with the `--socket` argument. The
`--socket` argument optionally takes a host address and port
(e.g. `--socket localhost:4000`), but will listen to all hosts at a
system-assigned port if no host address and port are provided.

When launched with `--socket`, Quahl will print a message of the form
`{"QuahlIPCSocket": "ADDRESS:PORT"}\r\n\r\n` upon startup, which can be parsed
by the launching process to get the address for the TCP socket to connect to.

The socket is closed automatically when the last window is closed and Quahl
will exit as normal.

## Interface

The interface provided is based on JSON-RPC 2.0, with two caveats:

### Calls must be terminated with CR LF CR LF

Because the connection is persistent, every remote procedure call has to
be terminated by two CRLF sequences (i.e. `\r\n\r\n`) before they will be
processed (responses, if any, are similarly followed by two CRLF sequences).
The advantage this has is that parsing of the bytestream exchanged between the
programs is easier, and you can maintain the connection persistently as long as
Quahl is running.

For obvious reasons, it is recommended that linebreaks for formatting of a
request object (or batch) are encoded only as a single LF (`\n`), never as a
CR LF sequence.

### Push messages

Second, in a way that does not conform to JSON-RPC 2.0, Quahl will also send
*push messages* to the client. These push messages are essentially server
responses without a prior remote procedure call (parallel to JSON-RPC's
client-issued *notifications*).

Push messages are implemented as response objects with a fixed *id* value of
`--push-msg`. You should therefore avoid using the string `--push-msg` as an
*id* for request objects. If you are not interested in the push messages, you
can safely ignore any responde objects with the `--push-msg` id.

Push messages are used to inform the client about activity (often
user-triggered) in the Quahl Browser App, such as the creation of a new window,
navigation to a new URL, when a window has been closed, when the App is about
to exit, etc. (These are yet to be implemented and/or documented).

## Procedures

### Controlling Browser Windows

#### create_window([*initial_url*: str]) -> *window_UUID*: str

Creates a new window and returns the UUID for the newly created window. If
*initial_url* is provided, Quahl will attempt to open that URL in the new
window. (Use `get_window_info()` or listen to push notifications to confirm
whether the URL was successfully loaded.)

#### close_all_windows() -> *success*: bool

Close all open windows. Typically this will result in the App exiting and the
socket closing. However, if used within a batch of calls and followed by at least
one `create_window()` call, the App will not terminate -- this is what makes it
distinct from `exit()`.

#### close_window(*window_UUID*: str) -> *success*: bool

Close the window with the specified UUID. Returns `true` if there was a window
open with such a UUID and it has been closed, `false` if no such window was
found (e.g. because the user has already closed it).

#### get_window_info(*window_UUID*: str) -> *window_info*: {*uuid*: str, *url*: str, *is_popup*: bool, *toolbar_visible*: bool, *active*: bool}

Returns an object with different information (UUID, current URL, whether it is
a popup window, whether the toolbar is visible, whether it is the active focused
window) about the window with the given UUID. Returns an empty object `{}` if
no window with the specified UUID exists (e.g. because it has been closed).

#### get_windows() -> *window_UUIDs*: array[str]

Returns a list with the UUIDs of all the currently open windows.

#### set_window_url(*window_UUID*: str, *url*: str) -> null

Requests that the window with UUID navigate to the specified URL. Note that this
can fail for a variety of reasons (window already closed, invalid URL, network
issues, invalid certificate), and you need to use calls to e.g.
`get_window_info()` or listen to push messages to confirm success.

#### set_window_icon(*window_UUID*: str, *url*: str) -> *success*: bool

Requests that the icon for the specified window be set to the file found at
*url*. It is recommended that *url* be the `file://` protocol path to a local
file that will be readable by Quahl. Returns `true` if the file was loaded and
set as the window's icon successfully, `false` otherwise.

Note that the icon is not persistent. If the user navigates to a different page
which specifies its own icon, the icon will be replaced. To achieve a persistent
effect, you have to listen to push messages and reset the icon every time a new
page has been loaded in the window. Therefore, if you are able to control the
resource navigated to, it is much better to specify the correct icon there (e.g.
as an HTML favicon).

#### set_window_toolbar_visible(*window_UUID*: str, *visible*: bool) -> *success*: bool

Sets the toolbar (forward, back, reload, address bar, download manager) for the
specified window to visible (`true`) or invisible (`false`). This will be done
irrespective of whether the window did originally display its toolbar or not,
but note that it does not make the address bar of popup windows editable in any
case.

### Controlling Downloads

#### initiate_download(*url*: str) -> *initiated*: bool

Initiates a new download request for the resource at the specified *url*. The
return value merely indicates whether the request has been issued successfully,
not that it will be accepted or successful (e.g. the resource may be blocked,
network problems may occur, the app may exit prematurely, the user might
cancel the download, etc.).

#### get_downloads() -> *downloads*: list[{*filename*: str, *status*: str}]

Returns a list of currently in progress and recently completed downloads. Each
entry is an object with the target filename to where it is saved, and the status
(e.g. 'completed', 'in progress', 'paused', 'cancelled'). Note that this
reflects the history showin in the download manager, so if the user clears the
list or removes an entry, those removed entries will not appear in the list.

### Controlling the Browser App

#### close_socket() -> null

Close the TCP socket and terminate all current connections, but keep the Browser
App running as normal otherwise.

#### exit() -> null

Terminate the app. Implies closing the socket.