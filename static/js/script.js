// Global variables
var species, n_trees, jsonOutput, getEverySec; 
var numFilters = 0;
var currReq = {
    "url": '',
    "idx": NaN,
    "properties": '',
    "values": ''
}
// Init leaflet map
var map = L.map('mapContainer').fitWorld();

window.onload = () => {
    // Load stats on start
    $.get('/stats', (data) => {
        n_trees = data['n_trees'];
        $('#numTrees').html(n_trees);
        $('#numSpecies').html(data['n_species']);
        $('#nTrees').html(n_trees-1);
    });
}

window.onscroll = () => {
    var scrolled = $(window).scrollTop();
    if (scrolled > 0) {
        $('#navbar').addClass('scrolled');
    } else {
        $('#navbar').removeClass('scrolled');
    }
}


// Show all species in the databank
showSpecies = () => {
    if (typeof species == 'undefined') { // Avoid unnessesary calls on backend
        $.get('/listspecies', data => {
            species = data["species"];
            $('#speciesList').attr('style', 'columns:' + parseInt(species.length / 11 + 1));
            species.forEach(specie => {
                $('#speciesList').append($('<li>' + specie + '</li>'));
            });
        })
    }
    $('#animAnchor').attr('class', 'moveWelcomeLeft');        
}

// Get tree item by index
getItem = () => {
    var idx = $('#idx').val();
    if (idx >= n_trees || idx < 0) {
        $('#idx').addClass('warning').next().show();
    }
    if (idx != '' && idx < n_trees && idx > -1){
        // Remove warning
        $('#idx').removeClass('warning').next().hide();
        // Do get
        $.get('/getitem/' + idx, data => {
            currReq.url = '/getitem/' + idx;
            currReq.idx = idx;
            var jsonStr = data['item'];
            // Update jsonOutput
            jsonOutput = jsonStr;
            var jsonObj = JSON.parse(jsonStr);
            // Clear previous results
            $('#jsonViewerContainer').empty();
            // Write new result
            $('#jsonViewerContainer').html('<pre id="idSearchRes"></pre>');
            $('#idSearchRes').jsonViewer(jsonObj, {rootCollapsable: false, withLinks: false});

            // Draw map
            drawMap([jsonObj]);
        });
        $('#numResContainer').hide();
        $('#treeTabs').hide();
        $('#saveAllButton').hide();
        $('#savePointCButton').hide();
        $('#saveCSVButton').hide();
        $('#jsonSnippetSection').show();
        $('#jsonViewerContainer').css('padding-bottom', '0');
        $('html,body').animate({
            scrollTop: $('#jsonSnippetSection').offset().top - 62},
            'slow');
    }
}

// Query trees via properties and value
searchDB = () => {
    // ======================== dummy ==============
    // var data = {
    //     "or": [
    //         {
    //             "species": "Acer Campestre"
    //         },
    //         {
    //             "species": "Betula pendula",
    //             "mode": "TLS",
    //             "Canopy Condition": "leaf-on"
    //         }
    //     ] 
    // };
    // var data2 = {
    //     "mode": "TLS",
    //     "canopy Condition": "leaf-on",
    //     "or": [
    //         {
    //             "species": "Acer Campestre"
    //         },
    //         {
    //             "species": "Betula pendula"
    //         }
    //     ]
    // };
    // console.log(JSON.stringify(data));
    // $.post('/search', JSON.stringify(data));
    // =============================================

    // Stores the outer most layer 
    // e.g. jsonObjs = [{'specie':'abies'}, {'mode':'tls'}]
    var jsonObjs = [];
    var nthFilter = 0;
    var nthOr = 0;
    $('.paramPair').each((index, e) => {
        var op = $(e).find('.filterOperand').text();
        var label = $(e).find('.fieldLabel').text();
        var value = $(e).find('.fieldValue').text();
        var classlists = e.classList;
        
        var obj = {};
        // (without brackets right now)
        if (nthFilter == 0) {
            obj[label] = value;
            jsonObjs.push(obj);
            nthFilter++;
        } else if (op == 'OR') {
            let hasPrevOr, key;
            let lastobj = jsonObjs[jsonObjs.length - 1];
            // check if the last obj of jsonObjs is OR array
            for (key in lastobj) {
                if (lastobj.hasOwnProperty(key) && /or*/.test(key)) {
                    hasPrevOr = true;
                }
            }
            if (hasPrevOr) {  // directly add to the OR array
                obj[label] = value;
                lastobj[key].push(obj);
            } else {
                let orArr = [];  // create a new OR array
                obj[label] = value;
                orArr.push(obj);  // push the current filter to array
                orArr.push(lastobj);  // push the prev filter to array
                jsonObjs.pop();  // remove the prev filter from jsonObjs
                let orObj = {};
                orObj['or' + nthOr] = orArr;
                jsonObjs.push(orObj);
                nthOr++;
            }
        }
    });
    
    // Store jsonObjs into one json:
    // e.g. jsonOut = {'specie':'abies', 'mode':'tls'}
    var jsonOut = {};
    jsonObjs.forEach(obj => {
        Object.keys(obj).forEach(key => jsonOut[key] = obj[key]);
    })
    
    console.log(jsonOut);

    // // Collect fields and values
    // const [properties, values] = collectFilterParams();

    // // Do GET
    // if (properties != '' && values != '') {
    //     $.get('/trees/' + properties + '/' + values, data => {
    //         currReq.url = '/trees/' + properties + '/' + values;
    //         currReq.properties = properties;
    //         currReq.values = values;
    //         var trees = data['query'];
    //         var num;
    //         // Clear previous results
    //         $('#jsonViewerContainer').empty(); 
    //         // Show number of results
    //         $('#numRes').html(trees.length);
    //         // Show json code snippets if trees found
    //         if (trees.length != 0) {
    //             $('#numResContainer').show();
    //             $('#saveAllButton').show();
    //             $('#savePointCButton').show();
    //             $('#saveCSVButton').show();
    //             // Update for output
    //             jsonOutput = JSON.stringify(trees[0]);
    //             // Show tabs if results > 1
    //             if (trees.length >= 3) {
    //                 num = 3;
    //                 $('#previewLabel').attr('style', 'display: inline;');
    //                 $('.treeTab').removeClass('active');
    //             } else {
    //                 num = trees.length;
    //                 $('#previewLabel').hide();
    //                 if (num == 1) {
    //                     $('#treeTab1').hide();
    //                 }
    //                 $('#treeTab2').hide();
    //             }
    //             // Show json data of maximal 3 trees
    //             for (let i = 0; i < num; i++) {
    //                 // Show tabs
    //                 $('#treeTabs').css('display', 'flex');
    //                 $('#treeTab' + i).show();
    //                 // Load data into html
    //                 $('#jsonViewerContainer').append('<pre class="previewTree" id="tree-' + i + '"></pre>');
    //                 $('#tree-' + i).jsonViewer(trees[i]);
    //                 // Show only one code block
    //                 if (i > 0) {
    //                     $('#tree-' + i).hide();
    //                 }
    //             }
    //             $('#treeTab0').children().addClass('active');

    //             // Draw map
    //             drawMap(trees);
    //         }
    //     });
    //     $('#jsonSnippetSection').show();
    //     $('#jsonViewerContainer').css('padding-bottom', '85px');
    //     $('html,body').animate({
    //         scrollTop: $('#jsonSnippetSection').offset().top - 62},
    //         'slow');
        
    //     // dummy partial implementation Point Clouds download
    //     if (values.includes('Pinus sylvestris')) {
    //         $('#savePointCButton').removeAttr('disabled');
    //     } else {
    //         $('#savePointCButton').attr('disabled', 'disabled');
    //     }
    // }
}
// Collect fields and values
collectFilterParams = () => {
    var properties = '';
    var values = '';
    $('.searchField').each((index, e) => {
        var field = $(e).text()
        var val = $(e.parentNode.nextElementSibling.children[0]).text();
        // Check emptiness
        if (field != 'Select search field') {
                if (field == 'Canopy') {
                    properties += 'canopy_condition,';
                    values += val + ',';
                } else if (field == 'Quality') {
                    var qFrom = $('.qualityFrom').eq(index);
                    var qTo = $('.qualityTo').eq(index);
                    // Only when from and to are both given, add to search properties
                    if (qFrom.text() != 'value' && qTo.text() != 'value') {
                        properties += 'quality,';
                        values += qFrom.text() + ',' + qTo.text() + ',';
                    } else if (qFrom.text() == 'value') {
                        qFrom.addClass('warning');
                        $('#searchButton').prop('disabled', true);
                        return;
                    } else if (qTo.text() == 'value') {
                        qTo.addClass('warning');
                        $('#searchButton').prop('disabled', true);
                        return;
                    }
                } else if (val != 'Please select a field first' && 
                           val != 'Choose a value') {
                    properties += field + ',';
                    values += val + ',';
                }
        }
    })
    properties = properties.toLowerCase().slice(0, -1);
    values = values.slice(0, -1);
    return [properties, values];
}

// Show download progress
showDlProgress = () => {
    $('#downLoadProgressSection').show();
    getEverySec = setInterval(getDlProgress, 1000);
}
// Get download progress
getDlProgress = () => {
    $.get('/progress', response => {
        $('#dlState').text(response['currItem'] + ' of ' + response['numAllItems'] + ' files zipped');
        var percentage = Math.round(response['currItem']/response['numAllItems']*100);
        $('#progressBar').attr('aria-valuenow', percentage).css('width', percentage + '%');
        if (response['currItem'] == response['numAllItems']) {
            clearInterval(getEverySec);
            $('#downLoadProgressSection').hide();
            $('#dlState').text('');
            $('#progressBar').attr('aria-valuenow', 0).css('width', '0%');
        }
    })
}

// Utility function: save a string to a file that will pop up for the user to download
saveContent = (fileContents, fileName) => {
    var link = document.createElement('a');
    link.download = fileName;
    link.href = 'data:,' + fileContents;
    link.click();
}
// Save single jsonOutput to a json file
saveJsonOutput = () => {
    saveContent(jsonOutput, 'current_tree_json.json');
}
// Save all result jsons into one json file
saveAllJsons = () => {
    var outString = '{"type": "FeatureCollection", "features":';
    $.get(currReq.url, data => {
        outString += JSON.stringify(data['query']) + '}';
        saveContent(outString, 'res_feature_collection.json');
    })
}
// Save all results into a csv file
saveCSV = () => {
    var link = document.createElement('a');
    link.download = 'csv.zip'
    link.href = '/exportcsv/' + currReq.properties + '/' + currReq.values;
    link.click();
}
// Save point clouds of all results into a zip
savePointClouds = () => {
    var zip = new JSZip();
    var cntFilesDownloaded = 0;
    $.get('/list_pointclouds', data => {
        // Show progress bar if request successful
        $('#downLoadProgressSection').show();
        // Iterate through the list of urls
        data['urls'].forEach((url, idx, array) => {
            var filename = url.split('/')[4];
            // Get request
            $.ajax({
                url: url,
                beforeSend: jqXHR => {
                    jqXHR.setRequestHeader('Accept-Encoding', 'gzip');
                },
                xhrFields:{
                    responseType: 'blob'
                }
            }).done(file => {
                // Add each file to the zip
                zip.file(filename, file, {binary: true, compression : "DEFLATE"});
                cntFilesDownloaded += 1;
                // Update progress
                $('#dlState').text(cntFilesDownloaded + ' of ' + array.length + ' files zipped');
                var percentage = Math.round(cntFilesDownloaded / array.length * 100);
                $('#progressBar').attr('aria-valuenow', percentage).css('width', percentage + '%');
                // After all files zipped
                if (cntFilesDownloaded === array.length) {
                    // Show zipping status
                    $('#pcState').text('Zipping...');
                    $('#dlState').text('');
                    // Create the zip file for download
                    zip.generateAsync({type : "blob", compression : "DEFLATE"})
                        .then(content => {
                            var link = document.createElement('a');
                            link.download = 'pointclouds';
                            link.href = URL.createObjectURL(content);
                            link.click();
                            // Hide progress bar and reset 
                            $('#downLoadProgressSection').hide();
                            $('#dlState').text('');
                            $('#progressBar').attr('aria-valuenow', 0).css('width', '0%');
                    });
                }
            })
        });
    })
}


// Add filter
addSearchFilter = e => {
    var field = e.text;
    var newFilterID = 'paramPair' + numFilters++;
    var andOp = '<span class="andOp filterOperand" onClick="toggleOp(this)">AND</span>';
    var addFilterCodeSnippet = 
        '<div class="wrapper paramPair removeFilterAble" id="'+ newFilterID + '" >' +
            '<span class="crossBtn" onclick="removeSearchFilter(this)"></span>' + andOp +
            '<div class="dropdown normalValUI" style="display: inline-block; width: calc(100% - 4rem);">' + 
                '<span class="fieldLabel ' + field + '">' + field + '</span><a class="btn btn-light dropdown-toggle fieldValue" role="button" data-bs-toggle="dropdown" aria-expanded="false">---</a>' + 
                '<ul class="dropdown-menu availableValues" aria-labelledby="fieldValue"></ul>' + 
            '</div>' + 
            '<span class="leftArrow parentheseArrow" onclick="moveLeft(this)"></span>' +
            '<span class="rightArrow parentheseArrow" onclick="moveRight(this)"></span>' + 
        '</div>';
    
    if ($('[id^="paramPair"]').length == 0) {  // If no filter exists yet
        $('.addFilter:first').before(addFilterCodeSnippet);  // Insert the first filter
        // $('.filterOperand:first').remove();
        // $('.dropdown.normalValUI').css('width', '100%');
        $('.filterOperand:first').text('.').removeClass('andOp').removeClass('orOp').addClass('firstFilter');
    } else {  // Otherwise insert code after the last filter, and add connecting operand
        $('[id^="paramPair"]:last').after(addFilterCodeSnippet);
    }
    
    // Update available values in the dropdown according to the added field filter
    updateAvailableVals(newFilterID, field);
}
//Remove filter
removeSearchFilter = e => {
    var rFilter = $('#' + e.parentNode.id)
    var nFilter = rFilter.next()
    rFilter.remove();
    // If the first filter is removed, the second becomes first, change style
    if (nFilter.prev().length == 0) {
        // $('.filterOperand:first').remove();
        // $('.paramPair:first').children('.dropdown').css('width', '100%');
        $('.filterOperand:first').text('.').removeClass('andOp').removeClass('orOp').addClass('firstFilter');
    } 
}
// After adding a filter, the available values will be updated in the dropdown
updateAvailableVals = (newFilterID, field) => {
    var e = $('#' + newFilterID);
    var fieldLabelEl = e.children().eq(-3).children()[0];
    var availableValuesEl = fieldLabelEl.nextElementSibling.nextElementSibling;

    switch (field) {
        case "Specie":
            $.get('/listspecies', data => {
                data["species"].sort().forEach(specie => {
                    $(availableValuesEl).append(
                        '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + specie + '</a></li>'
                    );
                });
            })
            break;
        case "Mode":
            var modes = ['TLS', 'ALS', 'ULS'];
            modes.forEach(mode => {
                $(availableValuesEl).append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + mode + '</a></li>'
                );
            })
            break;
        case "Canopy":
            var canopy_conditions = ['leaf-on', 'leaf-off'];
            canopy_conditions.forEach(cond => {
                $(availableValuesEl).append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + cond + '</a></li>'
                );
            })
            break;
        case "Quality":
            break;
        default:
            break;
    }
}
// Toggle and/or operands
toggleOp = e => {
    // Only or operand is allowed to combine multiple species filters 
    if ($(e).prev().text().startsWith('Specie') && $(e).next().text().startsWith('Specie')) {
        return;
    }
    if ($(e).text() === 'AND') {
        $(e).text('OR');
        $(e).removeClass('andOp').addClass('orOp');
    } else {
        $(e).text('AND');
        $(e).removeClass('orOp').addClass('andOp');
    }
}
// Update dropdown text when users selects a value
fieldValueSelected = e => {
    var fieldValueEl = e.parentNode.parentNode.previousElementSibling;
    $(fieldValueEl).html(e.text).attr('style', 'color: #212529');
}
// Move a single filter right (Add brackets)
moveLeft = e => {
    var classList = e.parentNode.classList;
    var classList = e.parentNode.classList;
    if (classList.contains('bracket-3')) {
        classList.remove('bracket-3');
    } else if (classList.contains('bracket-2')) {
        classList.remove('bracket-2');
    } else if (classList.contains('bracket-1')) {
        classList.remove('bracket-1');
    }
}
// Move a single filter left (Delete brackets)
moveRight = e => {
    var classList = e.parentNode.classList;
    if (!classList.contains('bracket-1')) {
        classList.add('bracket-1');
    } else if (!classList.contains('bracket-2')) {
        classList.add('bracket-2');
    } else if (!classList.contains('bracket-3')) {
        classList.add('bracket-3');
    }
}
qualityFrom = e => {
    var qualityFromEl = e.parentNode.parentNode.previousElementSibling;
    var qualityToEl = qualityFromEl.parentNode.nextElementSibling.nextElementSibling.children[0];
    $(qualityFromEl).html(e.text).attr('style', 'color: #000');
    checkQBounds(qualityFromEl, qualityToEl);
}
qualityTo = e => {
    var qualityToEl = e.parentNode.parentNode.previousElementSibling;
    var qualityFromEl = qualityToEl.parentNode.previousElementSibling.previousElementSibling.children[0];
    $(qualityToEl).html(e.text).attr('style', 'color: #000');
    checkQBounds(qualityFromEl, qualityToEl);
}
// Check if the quality lower bound is greater than upper bound 
checkQBounds = (from, to) => {
    var qErrEl = to.parentNode.nextElementSibling;
    if ($(from).text() > $(to).text()) {
        $(from).addClass('warning');
        $(to).addClass('warning');
        $(qErrEl).show();
        $('#searchButton').prop('disabled', true);
        return false;
    } else {
        $(from).removeClass('warning');
        $(to).removeClass('warning');
        $(qErrEl).hide();
        $('#searchButton').prop('disabled', false);
        return true;
    }
}
// Check if the selected field in additional filter is already given 
// fieldIsSafe = (field) => {
//     var isSafe = true;
//     $('.searchField').each((index, e) => {
//         if ($(e).text() == field) {
//             isSafe = !isSafe
//             return false;
//         }
//     })
//     return isSafe;
// }


// Toggle shown (active) tree data
toggleTab = e => {
    // Toggle active tabs
    $('.treeTab').removeClass('active');
    $(e).addClass('active');
    // Toggle shown data
    $('.previewTree').hide();
    $('#tree-' + (e.text - 1)).show();
    // Update jsonOutput
    jsonOutput = $('#tree-' + (e.text - 1)).text();
}

// Slide back to welcome
slideBack = () => {
    $('#animAnchor').attr('class', 'moveWelcomeBack'); 
}

// Trigger search when key enter is pressed in the search input bar
$('#idx').keydown(e => {
    if (e.which == 13) {
        getItem();
    }
});




//////////////////////////////////////////////////////////////////////////
//  Leaflet                                                             //
//////////////////////////////////////////////////////////////////////////
// Set up the tile layer
L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Data © <a href="http://osm.org/copyright">OpenStreetMap</a>',
    maxZoom: 18
}).addTo(map);
// Init geoJSONLayer(group)
var geoJSONLayer = L.geoJSON(null, {
        pointToLayer: function (feature, latlng) { // Each tree will be stored in one layer
            return L.marker(latlng);
        }
    }).addTo(map);

// Initialise the FeatureGroup to store drawing layers
var drawnItems = L.featureGroup().addTo(map);

var drawPluginOptions = {
  position: 'topright',
  draw: {
    polygon: {
        allowIntersection: false,
        showArea: true
    },
    polyline: false, // disable
    circle: false, 
    rectangle: false,
    marker: false,
    circlemarker: false
    },
  edit: {
    featureGroup: drawnItems, //REQUIRED!!
    poly: {
        allowIntersection: false
    }
  }
};

// Initialise the draw control and pass it the FeatureGroup of drawing layers
map.addControl(new L.Control.Draw(drawPluginOptions));

map.on(L.Draw.Event.CREATED, function (e) {
    var polyLayer = e.layer;
    drawnItems.addLayer(polyLayer);

    geoJSONLayer.eachLayer(marker => {
        if (marker instanceof L.Marker && isMarkerInsidePolygon(marker, polyLayer)) {
            marker._icon.classList.add("grayout");
            // map.removeLayer(marker);
        }
    });
});

map.on('draw:edited', function (e) {
    geoJSONLayer.eachLayer(marker => {
        marker._icon.classList.remove('grayout');
        drawnItems.eachLayer(poly => {
            if (marker instanceof L.Marker && isMarkerInsidePolygon(marker, poly)) {
                marker._icon.classList.add('grayout');
            }
        });
    });
});

map.on('draw:deleted', function(e) {
    var dLayers = e.layers;
    
    if (drawnItems.getLayers().length == 0) {
        geoJSONLayer.eachLayer(marker => {
            marker._icon.classList.remove('grayout');
        });
    } else {
        geoJSONLayer.eachLayer(marker => {
            dLayers.eachLayer(dPoly => {
                if (marker instanceof L.Marker && isMarkerInsidePolygon(marker, dPoly)) {
                    marker._icon.classList.remove('grayout');
                }
            });
        });
    }
});

// Check if a marker is inside a polygon
isMarkerInsidePolygon = (marker, poly) => {
    var polyPoints = poly.getLatLngs()[0];
    var x = marker.getLatLng().lat, y = marker.getLatLng().lng;

    var inside = false;
    for (var i = 0, j = polyPoints.length - 1; i < polyPoints.length; j = i++) {
        var xi = polyPoints[i].lat, yi = polyPoints[i].lng;
        var xj = polyPoints[j].lat, yj = polyPoints[j].lng;

        var intersect = ((yi > y) != (yj > y))
            && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
    }
    return inside;
};

// Show resulting trees on the map
drawMap = trees => {
    
    map.invalidateSize();  // Make sure tiles render correctly
    geoJSONLayer.clearLayers();  // Remove previous markers
    drawnItems.clearLayers(); // Remove previous polygons
    setTimeout(() => {
        // Add each tree to the geoJSONLayer. They will be displayed as markers by default
        trees.forEach(tree => {
            geoJSONLayer.addData(tree);
        });
        map.fitBounds(geoJSONLayer.getBounds()); // Fit the map display to results
    }, 100);

}


