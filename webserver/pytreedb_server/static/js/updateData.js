const fs = require('fs');
const path = require('path');
const geojsonDir = 'D:\\pytreedb\\pytreedb\\data\\geojson\\trees';

fs.readdir(geojsonDir, (err, files) => {
    if (err) {
        console.error('Error reading directory:', err);
        return;
    }
    files.forEach((file) => {
        if (path.extname(file).toLowerCase() === '.geojson') {
          const filePath = path.join(geojsonDir, file);
    
          fs.readFile(filePath, 'utf8', (err, data) => {
            if (err) {
              console.error(`Error reading file ${file}:`, err);
              return;
            }
    
            try {
    
              const geojson = JSON.parse(data);
    
    
              if (
                geojson.properties &&
                Array.isArray(geojson.properties.data)
              ) {
    
                geojson.properties.data = geojson.properties.data.map((item) => {
                  return { ...item, canopy_condition: null };
                });
              } else {
                console.warn(`No 'properties.data' array found in file ${file}`);
              }
    
    
              const updatedData = JSON.stringify(geojson, null, 2);
    
    
              fs.writeFile(filePath, updatedData, 'utf8', (err) => {
                if (err) {
                  console.error(`Error writing file ${file}:`, err);
                } else {
                  console.log(`Updated file: ${file}`);
                }
              });
            } catch (parseError) {
              console.error(`Error parsing JSON in file ${file}:`, parseError);
            }
          });
        }
      });
    });
