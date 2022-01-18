// Global variables
var speciesList, n_trees, jsonOutput, previewTrees = [], getEverySec; 
var numFilters = 0;
var currReq = {
    "url": '',
    "filters": [],
    "operands": [],
    "brackets": [],
    "stringFormat": '',
    "backendQ": ''
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
    // Get list of species on start to avoid redundant future calls
    $.get('/listspecies', data => {
        speciesList = data["species"].sort();
        $('#speciesList').attr('style', 'columns:' + parseInt(speciesList.length / 11 + 1));
        speciesList.forEach(specie => {
            $('#speciesList').append($('<li>' + specie + '</li>'));
        });
    })
    // Event handler for query import
    $('#queryUpload').change(() => {
        console.log($('#queryUpload')[0].files[0]);
        // Instantiate file reader
        const reader = new FileReader();
        var query = {};
        reader.onload = e => {
            query = JSON.parse(reader.result);  // Parse file
            replicateQuery(query);  // Replicate the query on page, so that users can further manipulate the query
            console.log(query);
        }
        // Read file
        reader.readAsText($('#queryUpload')[0].files[0]);
    })
}

window.onscroll = () => {
    var scrolled = $(window).scrollTop();
    if (scrolled > 0) {
        $('#navbar').addClass('scrolled');
    } else {
        $('#navbar').removeClass('scrolled');
    }
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
        $('#saveJsonButton').show();
        $('#saveAllButton').hide();
        $('#savePointCButton').hide();
        $('#saveCSVButton').hide();
        $('#mapContainer').show();
        $('#jsonSnippetSection').show();
        $('#jsonViewerContainer').css('padding-bottom', '0');
        $('html,body').animate({
            scrollTop: $('#jsonSnippetSection').offset().top - 62},
            'slow');
    }
}

// Query trees via properties and value
searchDB = () => {
    updateQueryPreview();
    let filters = currReq.filters, operands = currReq.operands, brackets = currReq.brackets;
    currReq.backendQ = processAND(0, currReq.filters.length - 1, filters, operands, brackets);

    $.post('/search', JSON.stringify({"data": currReq.backendQ}), data => {
        var trees = data['query'];
        currReq.url = '/search';
        // Clear previous results
        $('#jsonViewerContainer').empty(); 
        // Show number of results
        $('#numRes').html(trees.length);
        $('#numResContainer').show();
        // Show json code snippets if trees found
        if (trees.length != 0) {
            $('#saveJsonButton').show();
            $('#saveAllButton').show();
            $('#savePointCButton').show();
            $('#saveCSVButton').show();
            $('#mapContainer').show();
            // Update for output
            jsonOutput = JSON.stringify(trees[0]);
            // Show tabs if results > 1
            if (trees.length >= 3) {
                num = 3;
                $('#previewLabel').attr('style', 'display: inline;');
                $('.treeTab').removeClass('active');
            } else {
                num = trees.length;
                $('#previewLabel').hide();
                if (num == 1) {
                    $('#treeTab1').hide();
                }
                $('#treeTab2').hide();
            }
            // Show json data of maximal 3 trees
            for (let i = 0; i < num; i++) {
                // Show tabs
                $('#treeTabs').css('display', 'flex');
                $('#treeTab' + i).show();
                // Load data into html
                $('#jsonViewerContainer').append('<pre class="previewTree" id="tree-' + i + '"></pre>');
                $('#tree-' + i).jsonViewer(trees[i]);
                previewTrees.push(JSON.stringify(trees[i]))
                // Show only one code block
                if (i > 0) {
                    $('#tree-' + i).hide();
                }
            }
            $('#treeTab0').children().addClass('active');

            // Draw map
            drawMap(trees);
        } 
        // If no trees satisfy the query, clear prev results
        else {
            $('#previewLabel').hide();
            $('#treeTabs').hide();
            $('#saveJsonButton').hide();
            $('#saveAllButton').hide();
            $('#savePointCButton').hide();
            $('#saveCSVButton').hide();
            cleanMap();
            $('#mapContainer').hide();
        }
    });
    $('#jsonSnippetSection').show();
    $('#jsonViewerContainer').css('padding-bottom', '85px');
    $('html,body').animate({
        scrollTop: $('#jsonSnippetSection').offset().top - 62},
        'slow');
    
    // dummy partial implementation Point Clouds download
    if (currReq.filters.includes('species:pinus sylvestris')) {
        $('#savePointCButton').removeAttr('disabled');
    } else {
        $('#savePointCButton').attr('disabled', 'disabled');
    }
}
processAND = (start, end, ft, op, bk) => {
    let filters = ft.slice(start, end + 1); 
    let operands = op.slice(start, end + 1);
    let brackets = bk.slice(start, end + 1);
    
    // Check if the slice contains brackets
    if (!brackets.slice(1, end + 1).every((val, i, arr) => val === arr[0])) {
        // Split deeper brackets and go into another recursion
        let bracketOpen = false;
        let right = filters.length - 1, left = right - 1;
        while (left > -1) {
            if (brackets[right] > 0) {
                while (brackets[left] > 0) {
                    left -= 1;
                }
                // brackets = brackets.map(val => {return val - 1});
                let bracketL = processAND(left, right, filters, operands, brackets.map(val => {return val - 1}));
                filters.splice(left, right - left + 1, bracketL);
                operands.splice(left + 1, right - left);
                brackets.splice(left + 1, right - left);
                right = left - 1;
                left = right - 1;
            } else {
                bracketOpen = false;
                right -= 1;
                left = right - 1;
            }
        }
        return processAND(0, filters.length - 1, filters, operands, brackets);
    } else {
        // Process AND in this slice
        let prevIsAnd = false;
        for (let i = filters.length - 1; i > 0; i--) {
            if (operands[i] == "AND" && !prevIsAnd) {
                filters.splice(i - 1, 2, ['and', filters[i-1], filters[i]]);
                prevIsAnd = true;
            } else if (operands[i] == "AND" && prevIsAnd) {
                filters[i].push(filters[i-1])
                filters.splice(i - 1, 1);
            } else {
                prevIsAnd = false;
            }
        }
        return [filters];
    }
}
// Collect fields and values
collectFilterParams = () => {
    currReq.filters = [], currReq.operands = [], currReq.brackets = [];
    $('.paramPair').each((index, e) => {
        var op = $(e).find('.filterOperand').text();
        var label = $(e).find('.fieldLabel').text().toLowerCase();
        var value = $(e).find('.fieldValue').text().toLowerCase();
        var classlists = e.classList;
        var inBracket1 = classlists.contains('bracket-1');
        var inBracket2 = classlists.contains('bracket-2');
        var inBracket3 = classlists.contains('bracket-3');

        if (label.startsWith('canopy')) {label = 'canopy_condition'};
        
        currReq.filters.push(label + ':' + value);
        currReq.operands.push(op);
        currReq.brackets.push( inBracket3 ? 3 : ( inBracket2 ? 2 : ( inBracket1 ? 1 : 0 ) ) );
    });
}
// Show/update user-input query in human-readable string form
updateQueryPreview = () => {
    collectFilterParams();
    let newObj = jQuery.extend(true, {}, currReq);
    let filters = newObj.filters, operands = newObj.operands, brackets = newObj.brackets;

    let bracketOpen = 0;
    for (let i = filters.length - 1; i > -1; i--) {
        filters[i] = '\"' + filters[i] + '\"';
            if (bracketOpen < brackets[i]) {
                for (let n = 0; n < brackets[i] - bracketOpen; n++) {
                    filters[i] += ')';
                }
            }
            if (bracketOpen > brackets[i]) {
                for (let n = 0; n < bracketOpen - brackets[i]; n++) {
                    filters[i] = '(' + filters[i];
                }
            }
            bracketOpen = brackets[i];

        filters[i] = operands[i] + ' ' + filters[i];
    }
    
    currReq.stringFormat = filters.join(' ').substring(2);
    $('#queryPreviewArea').text(currReq.stringFormat);
    return currReq.stringFormat;
}
// Copy the query in preview to clipboard
// Referenced source: https://www.codegrepper.com/code-examples/javascript/copy+text+to+clipboard+javascript
copyQuery = () => {
    let targetText = $('#queryPreviewArea').text();
    if (!navigator.clipboard){ // use old commandExec() way
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val(targetText).select();
        document.execCommand("copy");
        $temp.remove();
    } else{
        navigator.clipboard.writeText(targetText);
    }    
}
// Export query for future use
exportQuery = () => {
    updateQueryPreview();
    if (currReq.backendQ == '') {
        let filters = currReq.filters, operands = currReq.operands, brackets = currReq.brackets;
        currReq.backendQ = processAND(0, currReq.filters.length - 1, filters, operands, brackets);
    }
    
    var queryJsonExp = {
        "queryString": currReq.stringFormat,
        "backendQuery": currReq.backendQ,
        "filters": currReq.filters,
        "operands": currReq.operands,
        "brackets": currReq.brackets
    };
    saveJsonContent(JSON.stringify(queryJsonExp), 'query_exported');
    querySaved = true;
}
// Import query
importQuery = () => {
    // Remind the user that importing will result in unsaved changes being discarded
    if (!confirm('Your current search will be discarded after importing.' +
        '(You could save your current query by exporting it to local.)\n' +
        'Continue import?')) {return;}

    $('#queryUpload').trigger('click');
}
// Replicate query
replicateQuery = query => {
    // Remove all current filters
    cleanSearchBar();
    // Add each filter to the page
    for (let i = 0; i < query.filters.length; i++) {
        // Styling
        let [lab, val] = capitalizeFirstLetter(query.filters[i].split(':'));
        if (lab === 'Mode') {val = val.toUpperCase();}
        if (lab.startsWith('Canopy')) {lab = 'Canopy';}
        // Add filter to page
        addSearchFilter({'text': lab});
        // Show the value of filter
        $('.fieldValue:last').html(val).attr('style', 'color: #212529');
        // Set the operand
        if (query.operands[i] == 'OR') {toggleOp($('.filterOperand:last'));}
        // Add brackets
        for (let depth = 1; depth <= query.brackets[i]; depth++) {
            moveRight($('.rightArrow:last')[0]);
        }
    }
    // Update query preview
    $('#queryPreviewArea').text(query.queryString); 
}
// Clean search
cleanSearchBar = () => {
    $('.paramPair').remove();
    $('#queryPreviewArea').text('Your query: ');
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

// Utility function: save a string to a txt file that will pop up for the user to download
// Source: https://stackoverflow.com/questions/283956/is-there-any-way-to-specify-a-suggested-filename-when-using-data-uri
saveContent = (fileContents, fileName) => {
    var link = document.createElement('a');
    link.download = fileName;
    link.href = 'data:,' + fileContents;
    link.click();
}
// Utility function: export an object to Json file for download
// Source: https://stackoverflow.com/questions/19721439/download-json-object-as-a-file-from-browser
saveJsonContent = (exportObj, fileName) => {
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(exportObj);
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", fileName + ".json");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}
// Save single jsonOutput to a json file
saveJsonOutput = () => {
    saveJsonContent(jsonOutput, 'current_tree_json');
}
// Save all result jsons into one json file
saveAllJsons = () => {
    var outString = '{"type": "FeatureCollection", "features":';
    if (currReq.url == '/search') {
        $.post('/search', JSON.stringify({"data": currReq.backendQ}), data => {
            outString += JSON.stringify(data['query']) + '}';
            saveJsonContent(outString, 'res_feature_collection');
        })
    } else {
        $.get(currReq.url, data => {
            outString += JSON.stringify(data['query']) + '}';
            saveJsonContent(outString, 'res_feature_collection');
        })
    }
}
// Save all results into zipped csv-files
saveCSV = () => {
    $.ajax({
        url: '/exportcsv',
        type: "POST",
        data: JSON.stringify({"data": currReq.backendQ}),
        success: file => {
            var link = document.createElement('a');
            link.href = window.URL.createObjectURL(file);
            console.log(link.href);
            link.download = 'csv.zip';
            document.body.appendChild(link);
            link.click();
        },
        xhrFields:{
            responseType: 'blob'
        }
    })
}
// Save point clouds of all results into a zip
// The JSZip library: https://github.com/Stuk/jszip
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
    var numQuality = 5;
        
    var normalFilterFVSnippet = 
        '<div class="dropdown fvWrapper" style="display: inline-block; width: calc(100% - 4rem);">' + 
            '<span class="fieldLabel ' + field + '">' + field + '</span><a class="btn btn-light dropdown-toggle fieldValue" role="button" data-bs-toggle="dropdown" aria-expanded="false">---</a>' + 
            '<ul class="dropdown-menu availableValues" aria-labelledby="fieldValue"></ul>' + 
        '</div>';
    var qualityFilterFVSnippet = 
        '<div class="fvWrapper" style="display: inline-block; width: calc(100% - 4rem);">' + 
            '<span class="fieldLabel ' + field + '">' + field + '</span>' + 
            '<div class="btn-light fieldValue" style="display: inline-block; color: #000">' + 
            qualityCheckboxes(numQuality) +
            '</div>'+
        '</div>';
    
    if ($('[id^="paramPair"]').length == 0) {  // If no filter exists yet
        // Insert the first filter
        if (field == 'Quality') {
            $('.addFilter:first').before(addWholeFilterSnippet(qualityFilterFVSnippet, newFilterID, andOp));  
        } else {
            $('.addFilter:first').before(addWholeFilterSnippet(normalFilterFVSnippet, newFilterID, andOp));
            // Update available values in the dropdown according to the added field filter
            updateAvailableVals(newFilterID, field);
        }
        $('.filterOperand:first').text('.').removeClass('andOp').removeClass('orOp').addClass('firstFilter');
    } else {  // Otherwise insert code after the last filter, and add connecting operand
        if (field == 'Quality') {
            $('[id^="paramPair"]:last').after(addWholeFilterSnippet(qualityFilterFVSnippet, newFilterID, andOp));
        } else {
            $('[id^="paramPair"]:last').after(addWholeFilterSnippet(normalFilterFVSnippet, newFilterID, andOp));
            updateAvailableVals(newFilterID, field);
        }
    }
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
// Build quality checkboxes
qualityCheckboxes = numQuality => {
    let out = "";
    for (let i = 1; i <= numQuality; i++) {
        out += 
        '<div class="form-check form-check-inline">' +
            '<input class="qualityCheckInput form-check-input" type="checkbox" id="qualityCheckbox' + i + '" value="' + i + '" />' +
            '<label class="form-check-label" for="qualityCheckbox' + i + '">' + i + '</label>' +
        '</div>';
    }
    return out;
}
// Add the complete html snippet for the new filter
addWholeFilterSnippet = (FVSnippet, newFilterID, andOp) => {
    return '<div class="wrapper paramPair removeFilterAble" id="'+ newFilterID + '" >' +
        '<span class="crossBtn" onclick="removeSearchFilter(this)"></span>' + andOp +
        FVSnippet + 
        '<span class="leftArrow parentheseArrow" onclick="moveLeft(this)"></span>' +
        '<span class="rightArrow parentheseArrow" onclick="moveRight(this)"></span>' + 
    '</div>';
}
// After adding a filter, the available values will be updated in the dropdown
updateAvailableVals = (newFilterID, field) => {
    var e = $('#' + newFilterID);
    var fieldLabelEl = e.children().eq(-3).children()[0];
    var availableValuesEl = fieldLabelEl.nextElementSibling.nextElementSibling;

    switch (field) {
        case "Species":
            speciesList.forEach(specie => {
                $(availableValuesEl).append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + specie + '</a></li>'
                );
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
            var canopy_conditions = ['Leaf-on', 'Leaf-off'];
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
    // if ($(e).prev().text().startsWith('Specie') && $(e).next().text().startsWith('Specie')) {
    //     return;
    // }
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


// Toggle shown (active) tree data
toggleTab = e => {
    // Toggle active tabs
    $('.treeTab').removeClass('active');
    $(e).addClass('active');
    // Toggle shown data
    $('.previewTree').hide();
    $('#tree-' + (e.text - 1)).show();
    // Update jsonOutput
    jsonOutput = previewTrees[e.text - 1];
}

// Show all species in the databank
showSpecies = () => {
    $('#animAnchor').attr('class', 'moveWelcomeLeft');        
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


// Other trivial helper functions
// Capitalize the first letter of each word in a list
capitalizeFirstLetter = arr => {
    let res = [];
    arr.forEach(string => {
        res.push(string.charAt(0).toUpperCase() + string.slice(1));
    });
    return res;
}

//////////////////////////////////////////////////////////////////////////
//  Leaflet                                                             //
//////////////////////////////////////////////////////////////////////////
// Leaflet Draw API: https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html

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
// Clean map, remove all markers and layers
cleanMap = () => {
    map.invalidateSize();  // Make sure tiles render correctly
    geoJSONLayer.clearLayers();  // Remove previous markers
    drawnItems.clearLayers(); // Remove previous polygons
}

