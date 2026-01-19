# 🎙️ Podcast Distribution Guide

This guide explains how to publish AudioNews daily briefings as podcasts on Spotify, Apple Podcasts, and other platforms.

## 📋 Overview

AudioNews generates RSS feeds for each language/service that can be submitted to podcast platforms:
- **English (UK)**: `https://audionews.uk/en_GB/podcast.rss`
- **Polish**: `https://audionews.uk/pl_PL/podcast.rss`
- **BellaNews**: `https://audionews.uk/bella/podcast.rss`

## ✅ Prerequisites

### 1. Podcast Artwork

Each podcast needs a square cover image (1400x1400px recommended):
- **Format**: PNG or JPG
- **Size**: Minimum 1400x1400px, maximum 3000x3000px
- **File size**: Under 500KB
- **Content**: Should represent the podcast brand

**Create artwork files:**
- `docs/images/podcast-cover-en-gb.png` - For English (UK)
- `docs/images/podcast-cover-pl-pl.png` - For Polish
- `docs/images/podcast-cover-bella.png` - For BellaNews

### 2. Email Address

Ensure `info@audionews.uk` (or your preferred email) is:
- Active and monitored
- Listed in the RSS feed (for verification)
- Accessible for platform verification emails

## 🎧 Publishing to Spotify

### Step 1: Create Spotify for Podcasters Account

1. Go to [Spotify for Podcasters](https://podcasters.spotify.com/)
2. Sign up or log in with your Spotify account
3. Verify your email address

### Step 2: Add Your Podcast

1. Click **"Add or claim your podcast"**
2. Select **"I have an RSS feed"**
3. Enter your RSS feed URL:
   - English: `https://audionews.uk/en_GB/podcast.rss`
   - Polish: `https://audionews.uk/pl_PL/podcast.rss`
   - BellaNews: `https://audionews.uk/bella/podcast.rss`
4. Click **"Next"**

### Step 3: Verify Ownership

- Spotify will send a verification email to the address in your RSS feed
- Check your email and click the verification link
- This confirms you own the podcast

### Step 4: Review and Submit

1. Review the podcast information (title, description, artwork)
2. Confirm the category and language settings
3. Click **"Submit for review"**

### Step 5: Approval

- Spotify typically reviews submissions within 24-48 hours
- Once approved, your podcast will appear on Spotify
- New episodes will automatically appear as they're published

## 🍎 Publishing to Apple Podcasts

### Step 1: Create Apple Podcasts Connect Account

1. Go to [Apple Podcasts Connect](https://podcastsconnect.apple.com/)
2. Sign in with your Apple ID
3. Accept the terms and conditions

### Step 2: Add Your Podcast

1. Click **"+"** to add a new show
2. Select **"Add a show with an RSS feed"**
3. Enter your RSS feed URL
4. Click **"Add"**

### Step 3: Review Information

1. Apple will fetch information from your RSS feed
2. Review and confirm:
   - Title
   - Description
   - Artwork
   - Category
   - Language
   - Explicit content setting

### Step 4: Submit for Review

1. Ensure all information is correct
2. Click **"Submit for Review"**
3. Apple reviews typically take 1-3 business days

## 📱 Other Platforms

### Google Podcasts
- Automatically indexes podcasts from RSS feeds
- No manual submission needed
- Ensure your RSS feed is publicly accessible

### Amazon Music & Audible
1. Go to [Amazon Music for Podcasters](https://podcasters.amazon.com/)
2. Sign in with Amazon account
3. Submit RSS feed URL
4. Wait for approval (typically 1-2 weeks)

### Pocket Casts
- Automatically discovers podcasts from RSS feeds
- No manual submission required

## 🔄 Automatic Updates

Once your podcast is live:
- **New episodes** are automatically added when the daily workflow runs
- **RSS feeds** are regenerated daily with the latest episodes
- **No manual intervention** needed - the system handles everything

## 📊 RSS Feed Details

### Feed Structure
- **Format**: RSS 2.0 with iTunes/Apple Podcasts extensions
- **Episodes**: Last 50 episodes (RSS best practice)
- **Update frequency**: Daily at 6 AM UK time
- **Audio format**: MP3
- **Metadata**: Includes full transcripts, descriptions, publication dates

### Feed Validation
Test your RSS feed before submitting:
- [Podbase RSS Validator](https://podba.se/validate/)
- [Cast Feed Validator](https://castfeedvalidator.com/)

## 🛠️ Troubleshooting

### RSS Feed Not Found
- Ensure the feed is accessible at the public URL
- Check GitHub Pages deployment is working
- Verify file exists: `docs/{language}/podcast.rss`

### Verification Email Not Received
- Check spam/junk folder
- Ensure email in RSS feed (`<managingEditor>`) is correct
- Verify email address is active

### Podcast Not Appearing
- Wait 24-48 hours after submission
- Check platform status page for review status
- Ensure RSS feed is valid and accessible

### Episodes Not Updating
- Verify RSS feed is regenerating daily
- Check workflow logs for RSS generation step
- Ensure audio files are being created successfully

## 📝 Customization

### Update Podcast Metadata

Edit `scripts/generate_podcast_rss.py` to customize:
- Titles
- Descriptions
- Categories
- Author information
- Email addresses

### Add More Languages

1. Add configuration to `PODCAST_CONFIG` in `generate_podcast_rss.py`
2. Add language to workflow RSS generation step
3. Create artwork for new language
4. Submit new RSS feed to platforms

## 🔗 Useful Links

- [Spotify for Podcasters](https://podcasters.spotify.com/)
- [Apple Podcasts Connect](https://podcastsconnect.apple.com/)
- [RSS 2.0 Specification](https://www.rssboard.org/rss-specification)
- [Apple Podcasts RSS Tags](https://help.apple.com/itc/podcasts_connect/#/itcb54353390)

## ✅ Checklist

Before submitting:
- [ ] Podcast artwork created (1400x1400px for each language)
- [ ] Artwork uploaded to `docs/images/`
- [ ] RSS feeds generated and accessible
- [ ] RSS feeds validated
- [ ] Email address verified and active
- [ ] At least 1 episode in RSS feed
- [ ] Audio files accessible via HTTPS

After submission:
- [ ] Verification email received and confirmed
- [ ] Podcast appears in platform directory
- [ ] Episodes are updating daily
- [ ] Audio playback works correctly
