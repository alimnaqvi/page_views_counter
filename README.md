# Page views counter

A FastAPI app that counts the number of times a web page was viewed. The app saves (in a PostgreSQL database) the number of requests to the server along with HTTP headers such as the user-agent.

## Usage

<p>
  After deploying the app to your favorite cloud platform (see ![deployment](#deployment) section below for some examples), embed the URL as an image on the page you want to monitor, e.g.:
  <img src="https://page-views-counter-534232554413.europe-west1.run.app/view?src=github.com&src_uri=/alimnaqvi/page_views_counter" style="display: none;" />
</p>

```html
<img src="https://your-deployment-url.com/view" alt="Page views counter" />
```

Or as Markdown:

```markdown
![Page views counter](https://your-deployment-url.com/view)
```

## Deployment

Below are some examples of deploying this app to a cloud service.

Regardless of where you deploy:
* Fork this repository first.
* Set up a PostgreSQL database as DATABASE_URL environment variable is required for this app to work.
  * Vercel makes it trivially easy to create a fully managed Postgres database in seconds [with Neon](https://vercel.com/integrations/neon) (this database can be used anywhere, even outside Vercel deployments).
  * In any case, you will need to save the connection string of a PostgreSQL database in an environment variable called DATABASE_URL.
  * For example, the format of the connection string is: "postgresql://[user]:[password]@[neon_hostname]/[dbname]?sslmode=require&channel_binding=require".
* (Optional) The [GITHUB_PROFILE_URL environment variable](#github-cache-clearing) can be optionally set if you want to count page views on your GitHub profile.

### Google Cloud Run

[Google Cloud Run](https://cloud.google.com/run) is a fully managed platform that enables you to run your code directly on Google Cloud Platform (GCP) infrastructure. It's a bit more finicky to set up than the below options, but the below options are actually using the infrastructure of hyperscalers like Google or AWS anyway.

Google has [very handy quickstart guides](https://cloud.google.com/run/docs/quickstarts/) but here are the high-level steps you need to follow:

1. After signing up for a [Google Cloud account](https://console.cloud.google.com/), go to [Cloud Run page](https://console.cloud.google.com/run) and select "Deploy container".
2. Select GitHub as the deployment source and then grant access to your copy of this repository by clicking on "Set up with Cloud Build".
3. After setting up source repository with Cloud Build, select Build Type as "Go, Node.js, Python, Java, .NET Core, Ruby or PHP via Google Cloud's buildpacks".
4. Keep the build directory as `/` and set the Entrypoint to `uvicorn main:app --host 0.0.0.0 --port $PORT` (leave the "Function target" blank). Click Save.
5. Most configuration options for the deployment can be left as default.
6. In "Containers, Volumes, Networking, Security" section withing the "Containers" tab and the "Variables & Secrets" tab within that, set the DATABASE_URL environment variable either directly, or better, as a secret.
7. (Optional) To make the cache persist through app shutdown, mount a persistent storage volume such as [Google Cloud Storage](https://cloud.google.com/storage) to your container, then add CACHE_DIR environment variable to point to this volume.
8. Click on "Create". The deployment should now succeed.

### Full-stack cloud deployment services

On services such as [Render](https://render.com/) and [Railway](https://railway.com/), the deployment is simple:

1. Create a new project (of type "web service" for Render) by importing your copy of this repository.
2. Set the build command as `pip install -r requirements.txt && python init_db.py`.
3. Set the start command as `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. Set the DATABASE_URL environment variable.
5. The deployment should now succeed.

### Vercel

Note that Vercel's support for Python web apps is subpar. The method below uses legacy configuration (in vercel.json) that Vercel [advises against using](https://vercel.com/docs/project-configuration#builds).

Add the following `vercel.json` to your copy of this repository:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "python3 init_db.py",
  "devCommand": "uvicorn main:app",
  "framework": null,
  "outputDirectory": ".",
    "builds": [
      {
        "src": "main.py",
        "use": "@vercel/python"
      }
    ],
    "routes": [
      {
        "src": "/(.*)",
        "dest": "main.py"
      }
    ]
    
  }
```

Create a new Vercel project by importing your copy of this repository.

Set the DATABASE_URL environment variable and confirm deployment.

## GitHub cache clearing

For embedding the views counter on GitHub profile, an additional factor to keep in mind is Github's image caching system. After the first visit, the subsequent visitors do not cause Github to send a request to the deployed server, for hours and even days. Github documentation [mentions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-anonymized-urls) that `curl -X PURGE https://camo.githubusercontent.com/....` purges the cache and forces every GitHub user to re-request the image.

So I have added a mechanism in this Python app to purge the cache after sending back each response pixel. This is done by using [FastAPI's Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/). For this logic to work, an environment variable GITHUB_PROFILE_URL (and optionally GITHUB_CAMO_URL) must be set. To make the cache persist through app shutdown, CACHE_DIR environment variable must be set so that cache file can be saved in that directory. The logic in the Python app automatically gets the GitHub profile page, looks for GitHub camo URL on the page, and sends a PURGE request to clear the cache.
