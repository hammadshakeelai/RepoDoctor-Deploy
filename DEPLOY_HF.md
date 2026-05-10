# Deploy to Hugging Face Spaces

## 1. Sign up
- https://huggingface.co/join (free)

## 2. Create access token
- https://huggingface.co/settings/tokens → New token → role **Write** → copy

## 3. Create Space
- https://huggingface.co/new-space
- **Owner:** your username
- **Space name:** `repodoctor` (or any)
- **License:** mit
- **SDK:** **Docker** → **Blank**
- **Hardware:** CPU basic (free)
- **Public** (or private — free for personal)
- Click **Create Space**

## 4. Add OPENAI_API_KEY secret
- On the new Space page → **Settings** tab
- Scroll to **Variables and secrets** → **New secret**
- Name: `OPENAI_API_KEY`
- Value: your key from `.env`
- Save

## 5. Push code

In PowerShell, from `RepoDoctor-Deploy/`:

```powershell
git init
git add .
git commit -m "Initial RepoDoctor AI deploy"

# Replace USERNAME and SPACE_NAME with yours
git remote add space https://huggingface.co/spaces/USERNAME/SPACE_NAME

# Push (will prompt for HF username + access token as password)
git push space main
```

If your default branch is `master`:
```powershell
git push space master:main
```

## 6. Watch build
- Space page → **Logs** tab → Docker build runs (~6 min first time)
- When done, app appears in the Space frame
- Direct URL: `https://USERNAME-SPACE_NAME.hf.space`

## Updating
```powershell
git add . ; git commit -m "update" ; git push space main
```

## Troubleshooting

| Symptom                                | Fix                                                                  |
|----------------------------------------|----------------------------------------------------------------------|
| `git push` asks password               | Use the **HF access token** (not your account password).             |
| Build fails on `useradd`               | Already handled in our Dockerfile — re-pull repo.                    |
| App loads but `/api/analyze` 500       | `OPENAI_API_KEY` secret not set, or wrong name.                      |
| Container restarts every 30s           | Hardware tier too small — keep CPU basic, free.                      |
| `.env` accidentally committed          | `.gitignore` excludes it; verify with `git ls-files \| findstr env`. |

## Free-tier limits
- CPU basic: 2 vCPU, 16 GB RAM, ephemeral disk
- Auto-sleeps after ~48h idle (free tier); first hit wakes it (~30 s)
- For always-on / GPU → upgrade in Settings
