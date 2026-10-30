# Obsidian MCP Setup

Prerequisite for the `obsidian` skill. Configure once; reuse across all vaults/projects.

## 1. Install the plugin (per vault)

Install and enable **Local REST API with MCP** in Obsidian (Settings > Community plugins).
Source: https://github.com/coddingtonbear/obsidian-local-rest-api#readme

Each vault gets its own plugin instance and its own API Key (Settings > Local REST API > API Key).

In each vault, also enable **Enable Non-encrypted (HTTP) Server** (Settings > Local REST API). The default HTTPS endpoint (port 27124) uses a self-signed certificate that the Antigravity MCP client rejects (`x509: certificate signed by unknown authority`). The HTTP endpoint (port 27123) listens on loopback only, so traffic never leaves the machine.

## 2. Configure the MCP in Antigravity

```json
{
  "mcpServers": {
    "obsidian": {
      "type": "http",
      "enabledTools": [
        "search_query",
        "vault_read",
        "vault_get_document_map",
        "vault_patch",
        "vault_write",
        "vault_list"
      ],
      "url": "http://127.0.0.1:27123/mcp/",
      "headers": {
        "Authorization": "Bearer <YOUR_API_KEY>"
      }
    }
  }
}
```

`enabledTools` is an allowlist: only the tools the skill needs stay exposed (the other 10 are hidden to keep context lean and avoid destructive tools such as `vault_delete`/`vault_move`).

| Scope | File |
| :--- | :--- |
| Global (all projects) | `~/.gemini/config/mcp_config.json` |
| Per project | `.agents/mcp_config.json` (add to `.gitignore`: it holds the token) |

Restart the session/chat after editing.

## 3. One API Key for all vaults (recommended)

To avoid editing the Antigravity MCP config per project:

1. Pick the API Key you configured in step 2.
2. In every other vault, open `<vault>/.obsidian/plugins/obsidian-local-rest-api/data.json`.
3. Replace the `apiKey` value with that same key (with Obsidian closed, or reload the plugin afterwards).

Result: one global MCP config works for every vault.

## 4. Runtime requirements

- Obsidian must be **open**, with the **project's vault selected**.
- Only one vault can serve at a time: all vaults share port `27123`, so keep a single vault open.
- Switching vault = the MCP now reads/writes that vault; confirm it before patching.

## Troubleshooting

| Symptom | Cause / Fix |
| :--- | :--- |
| Connection refused | Obsidian closed, plugin disabled, or wrong vault open |
| `Server not initialized` | Request sent without MCP `initialize` handshake (client issue, not server) |
| 401 / unauthorized | `apiKey` in the open vault differs from the one in `mcp_config.json` |
| `x509: certificate signed by unknown authority` | Using the HTTPS endpoint (27124, self-signed). Enable the HTTP server in the plugin and use `http://127.0.0.1:27123/mcp/`. Alternative: import the plugin's `.crt` into the Windows Trusted Root store |
| Tools not appearing | Restart session; check **... > MCP Servers** |

## Security

Never commit the API Key. It grants read/write access to the vault. Rotate it if exposed.

