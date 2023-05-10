# GIT UPDATES TO OPS BRANCH

March 2022
nadya.moisseeva@hawaii.edu

Below are some notes on how to update the 'ops' branch of the vog pipeline with changes on 'master'

# Save current working setup
- Make sure you are on 'ops' branch 
- Make sure no changes need to be committed and everything is pushed to remote

# Update 'master' branch
- Switch to master branch
- Pull latest updates from remote

# Start the merge on 'ops' branch
- Switch back to 'ops'
- Run merge with no auto-commit
```
git merge master --no-commit --no-ff
```

# Work through changes
- Edit individual files to remove conflict and wrong settings for ops pipeline
- Add each individaul file that's been modified

# Finialize commit
- check git status and commit changes
- push ops to remote



