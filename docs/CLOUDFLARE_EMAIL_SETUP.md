# Cloudflare Email Routing Setup for team@sandraschi.dev

**Purpose**: Set up email forwarding so `team@sandraschi.dev` forwards to your existing email address.

## Prerequisites

1. Domain registered (sandraschi.dev)
2. Domain added to Cloudflare (DNS managed by Cloudflare)

## Setup Steps

### 1. Add Domain to Cloudflare

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Click "Add a Site"
3. Enter `sandraschi.dev`
4. Follow the setup wizard to update nameservers at your domain registrar

### 2. Enable Email Routing

1. In Cloudflare dashboard, select your domain
2. Go to **Email** → **Email Routing**
3. Click **Get Started**
4. Cloudflare will automatically add the required DNS records (MX, TXT)

### 3. Create Email Address

1. In Email Routing, go to **Routing** tab
2. Click **Create address**
3. Enter:
   - **Email address**: `team`
   - **Destination**: Your existing email address (e.g., `yourname@gmail.com`)
4. Click **Save**

### 4. Verify Setup

1. Cloudflare will send a verification email to your destination address
2. Click the verification link in the email
3. Email routing is now active!

## Usage

- **Send emails TO**: `team@sandraschi.dev` → Forwards to your existing email
- **Send emails FROM**: You can also send emails from `team@sandraschi.dev` using Cloudflare's email API or SMTP

## Benefits

- ✅ **Free** - No cost for email routing
- ✅ **Easy setup** - Takes ~5 minutes
- ✅ **No separate mailbox** - Forwards to existing email
- ✅ **Professional** - Uses your custom domain
- ✅ **Consistent** - Use `team@sandraschi.dev` across all repos

## DNS Records (Auto-added by Cloudflare)

Cloudflare automatically adds these records:
- **MX records**: For receiving emails
- **TXT records**: For email routing verification

## Troubleshooting

- **Emails not arriving**: Check spam folder, verify DNS propagation
- **Verification failed**: Make sure you clicked the verification link
- **Domain not verified**: Ensure nameservers are correctly set at registrar

## Next Steps

Once set up, `team@sandraschi.dev` will work in:
- `manifest.json` (MCPB packages)
- `pyproject.toml` (Python packages)
- All your MCP server repositories

