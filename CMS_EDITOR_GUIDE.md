# Editing the site with Pages CMS

Pages CMS is a web form for the content files in this repository. Nothing you save goes live until Raj merges a pull request.

**You can edit:** Films, News posts, Team members, Shop products, Social links, and the pictures for them.
**You cannot edit:** the design, layout, build, hosting settings or any other file.

## 1. Sign in

1. Go to <https://app.pagescms.org> and choose **Sign in with GitHub**.
2. Open **SeahorseFilm / seahorsefilmhouse**. You need a GitHub account with write access to the repository; ask Raj if the repository is missing.

## 2. Always work on a `cms/` branch, never `main`

Before changing anything, use the **branch** menu at the top of the page and create a branch named `cms/<short-description>`, for example `cms/news-chasm-update`. Lower-case, hyphens, no spaces. Make sure that branch is selected while you edit.

Do not save on `main`. Saving on `main` would publish straight to the live site. Raj switches this off in GitHub (see "For Raj" below), but check the branch name every time.

## 3. Create or edit a news post

1. Choose **News posts**, then open the posts list.
2. To edit, open the post. To add one, use the add button at the end of the list.
3. Fill in:
   - **Title**: a short headline.
   - **Page address (slug)**: lower-case letters, numbers and hyphens, unique, for example `chasm-trailer-released`. It becomes the web address.
   - **Date**: pick the date.
   - **Summary**: one or two sentences, shown on cards and in search results.
   - **Picture** and **Alt text** (see section 6).
   - **Text**: one entry per paragraph, no `<p>` tags. Use `<em>text</em>` for italics. Link to a film as `<a href="../films/chasm.html">the Chasm page</a>`; any other link must start with `https://`.
   - **Sources** (optional): label and `https://` link.
   - Type everything as it should read, with real characters such as ’ or é. Do not type HTML codes such as `&rsquo;`.
4. Only publish facts that have been approved. Do not invent dates, quotes or credits. Do not add any Tokyo detail beyond what is already published.
5. Press **Save**. Red messages under a field tell you what to fix.

## 4. Edit a film

1. Choose **Films** and open the film.
2. Change only what you were asked to. Keep **Page address (slug)** as it is.
3. **Status** is either `Released` or `Upcoming`. Released films need director, runtime (like `102 min`), genre, cast, trailer link, trailer upload date and time, where to watch, JustWatch link and awards. Upcoming films need a stage such as `In development`.
4. Links must start with `https://`. The trailer must look like `https://www.youtube.com/watch?v=XXXXXXXXXXX`.
5. The order of films in the list is the order of the home-page film list. Do not reorder unless asked.
6. Press **Save**.

## 5. Team and shop

- **Team members:** name, role, IMDb link (`https://…`), photo with alt text.
- **Shop products:** to switch a product on, set **Availability** to `Available` and fill in **Price** and **Buy link**. To switch it off, set `Coming soon` and empty the buy link. The buy link is the product's own page. Never enter payment details.
- **Social links:** an empty link hides that profile.

## 6. Upload an image and write alt text

1. Choose **Media**, then **Pictures** (posters, stills, team and news pictures) or **Shop product photos**.
2. Upload a `.jpg` or `.png`. Any size is fine; the website makes the web sizes itself. Pictures only go into those two folders.
3. In the form, type the file's **exact name** in **Original file name** (for a new picture), then give a **Website file name**: lower-case, hyphens, ending `.jpg`, for example `news-chasm-trailer.jpg`. Never reuse a name.
4. To reuse a picture that already exists (for example a film poster), leave **Original file name** empty and give only its website file name, such as `poster-chasm.jpg`, and the alt text.
5. **Alt text** describes what the picture shows, for people using screen readers and for search engines. Write plain words, for example "Still from Open 24 Hours". Do not start with "image of". Every picture needs alt text.

## 7. Save to the branch, open a pull request, check the preview

1. Check you are still on your `cms/…` branch, then press **Save**. Pages CMS commits to that branch only.
2. Open the repository on GitHub (<https://github.com/SeahorseFilm/seahorsefilmhouse>). GitHub shows a banner for your recently pushed branch: press **Compare & pull request**. Give it a clear title and describe what you changed.
3. Wait for the Netlify checks on the pull request. If the build fails, the message says which file and field to fix; go back to Pages CMS on the same branch and correct it.
4. When the checks pass, open the **Deploy Preview** link in the pull request and look at the pages you changed on phone and desktop.
5. Ask Raj to review the pull request.

## 8. Merging publishes

**When Raj merges the pull request into `main`, the change goes live on seahorsefilmhouse.com about a minute later.** Until then nothing on the live site changes. To undo a mistake after publishing, tell Raj; it can be reverted.

## For Raj (one-time GitHub setup)

Pages CMS cannot stop a collaborator from picking `main` in its branch menu. Enforce the workflow in GitHub: **Settings → Branches (or Rules → Rulesets)**, add a rule for `main` that requires a pull request before merging and (recommended) that Netlify's deploy preview check passes. Only give write access to people who should edit. Also install the Pages CMS GitHub app on this repository only.
