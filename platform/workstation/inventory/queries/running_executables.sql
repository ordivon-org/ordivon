SELECT DISTINCT name, path
FROM processes
WHERE path != ''
ORDER BY path;
