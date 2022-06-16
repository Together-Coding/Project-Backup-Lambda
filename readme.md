# Project Backup Lambda

Periodically check the projects that have active flags but are actually not recently used.

For each projects that are in the conditions, the following processes are done:
1. Get file list from Redis
2. Get file contents from Redis too
3. Write file contents into temp directory
4. Zip the temp directory
5. Upload to S3
6. Remove the data from Redis
