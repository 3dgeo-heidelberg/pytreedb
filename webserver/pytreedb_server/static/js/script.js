// Global variables
var speciesList, n_trees, jsonOutput, previewTrees = [], getEverySec, pcUrls = []; 
var numFilters = 0;
var nthEntrySet = 0, elemMatch = false, maxPreviewLimit = 10, previewLimit = 3;
var currNumRes, prevNumRes;
var lazDlLimit = 1000;
var currReq = {
    "url": '',
    "filters": [],
    "qfilters": [],
    "operands": [],
    "brackets": [],
    "stringFormat": '',
    "backendQ": ''
}
var filterKeys = {
    "species": "properties.species",
    "mode": "properties.data.mode",
    "canopy_condition": "properties.data.canopy_condition",
    "quality": "properties.data.quality",
    "source": "properties.measurements.source",
    "dbh": "properties.measurements.DBH_cm",
    "height": "properties.measurements.height_m",
    "crowndia.": "properties.measurements.mean_crown_diameter_m"
}
// Init leaflet map
var map = L.map('mapContainer').fitWorld();
var index;
var ready = false;

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
        speciesList = data["species"];
        $('#speciesList').attr('style', 'columns: 3');
        speciesList.forEach(specie => {
            $('#speciesList').append($('<li>' + specie + '</li>'));
        });
    })
    // Event handler for query import
    $('#queryUpload').change(() => {
        // Instantiate file reader
        const reader = new FileReader();
        var query = {};
        // Read file
        reader.readAsText($('#queryUpload')[0].files[0]);
        reader.onload = e => {
            query = JSON.parse(reader.result);  // Parse file
            replicateQuery(query);  // Replicate the query on page, so that users can further manipulate the query
        }
    })

    // Init tooltips
    $(() => { $('[data-toggle="tooltip"]').tooltip() });

    setTimeout(() => {
        if (typeof query !== 'undefined') {
            replicateQuery(query);
            searchDB();
        }
    }, 600);
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
            var jsonObj = data['item'];
            // Update jsonOutput
            jsonOutput = JSON.stringify(data['item'], null, 2);
            // Clear previous results
            $('#jsonViewerContainer').empty();
            // Write new result
            $('#jsonViewerContainer').html('<pre id="idSearchRes"></pre>');
            $('#idSearchRes').jsonViewer(jsonObj, {rootCollapsable: false, withLinks: false});

            // Draw map
            drawMap([jsonObj]);
        });
        prevNumRes = null;
        $('#numResContainer').hide();
        $('#treeTabs').hide();
        $('#dlButtons').show();
        $('#saveJsonButton').show();
        $('#savePointCButton').show();
        $('#saveAllButton').hide();
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
    previewLimit = Math.min($('#numPreviewTrees').val(), maxPreviewLimit);
    nthEntrySet = 0;
    elemMatch = $('#elemMatchCheckbox')[0].checked;
    let renderMarkers = $('#markerRenderCheckbox')[0].checked;
    let qfilters = currReq.qfilters, operands = currReq.operands, brackets = currReq.brackets;
    currReq.backendQ = processAND(0, currReq.qfilters.length - 1, qfilters, operands, brackets, elemMatch);
    if (!currReq.backendQ) {currReq.backendQ = {};}

    // Send POST request to API endpoint specifically for webserver search request
    // where only a (user-defined) limited number of the first full-json documents are returned
    // along with coordinates of all resulting trees for rendering in the map if demanded
    $.when(queryBackend(elemMatch, previewLimit, nthEntrySet, renderMarkers, false))
        .then(numRes => prevNumRes = numRes);
    $('#jsonSnippetSection').show();
    $('#jsonViewerContainer').css('padding-bottom', '85px');
    $('html,body').animate({scrollTop: $('#jsonSnippetSection').offset().top - 62}, 'slow');
    // Update interface to show the number of results correctly
    $('.geoRes').hide();
    $('.normRes').show();
}
processAND = (start, end, ft, op, bk, elemMatch) => {
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
                let key1 = Object.keys(filters[i-1])[0], 
                    key2 = Object.keys(filters[i])[0];
                let obj1 = {}, obj2 = {};
                if (elemMatch && key1.startsWith('properties.data') && key2.startsWith('properties.data')) {
                    obj1[key1.split('.')[2]] = filters[i-1][key1];
                    obj2[key2.split('.')[2]] = filters[i][key2];
                    filters.splice(i - 1, 2, {"properties.data": {"$elemMatch": {"$and":[obj1, obj2]}}});
                } else if (elemMatch && key1.startsWith('properties.measurements') && key2.startsWith('properties.measurements')) {
                    obj1[key1.split('.')[2]] = filters[i-1][key1];
                    obj2[key2.split('.')[2]] = filters[i][key2];
                    filters.splice(i - 1, 2, {"properties.measurements": {"$elemMatch": {"$and":[obj1, obj2]}}});
                }  else {
                    filters.splice(i - 1, 2, {'$and': [filters[i-1], filters[i]]});
                }
                prevIsAnd = true;
            } else if (operands[i] == "AND" && prevIsAnd) {
                let key1 = Object.keys(filters[i-1])[0], 
                    key2 = Object.keys(filters[i])[0];
                let obj = {};
                if (elemMatch && key1.startsWith('properties.data') && key2.startsWith('properties.data')) {
                    obj[key1.split('.')[2]] = filters[i-1][key1];
                    filters[i]['properties.data']['$elemMatch']['$and'].push(obj);
                    filters.splice(i - 1, 1);
                } else if (elemMatch && key1.startsWith('properties.measurements') && key2.startsWith('properties.measurements')) {
                    obj[key1.split('.')[2]] = filters[i-1][key1];
                    filters[i]['properties.data']['$elemMatch']['$and'].push(obj);
                    filters.splice(i - 1, 1);
                } else if (filters[i]['$and']){
                    let andArr = filters[i]['$and'];
                    let nomatch = true;
                    if (elemMatch && (key1.startsWith('properties.data') || key1.startsWith('properties.measurements'))) {
                        for (let j = 0; j < andArr.length; j++) {
                            let object = andArr[j];
                            if (Object.keys(object)[0].startsWith('properties.data') && key1.startsWith('properties.data')) {
                                let obj1 = {}, obj2 = {};
                                obj1[key1.split('.')[2]] = filters[i-1][key1];
                                if (object['properties.data'] && object['properties.data']['$elemMatch']) {
                                    object['properties.data']['$elemMatch']['$and'].push(obj1);
                                } else {
                                    obj2[Object.keys(object)[0].split('.')[2]] = Object.values(object)[0];
                                    andArr.splice(j, 1, {"properties.data": {'$elemMatch': {'$and':[obj1, obj2]}}});
                                }
                                nomatch = false;
                            } else if (Object.keys(object)[0].startsWith('properties.measurements') 
                            && key1.startsWith('properties.measurements')) {
                                let obj1 = {}, obj2 = {};
                                obj1[key1.split('.')[2]] = filters[i-1][key1];
                                if (object['properties.measurements'] && object['properties.measurements']['$elemMatch']) {
                                    object['properties.measurements']['$elemMatch']['$and'].push(obj1);
                                } else {
                                    obj2[Object.keys(object)[0].split('.')[2]] = Object.values(object)[0];
                                    andArr.splice(j, 1, {'properties.measurements': {'$elemMatch': {'$and':[obj1, obj2]}}});
                                }
                                nomatch = false;
                            }
                        }
                        if (nomatch) {andArr.push(filters[i-1]);}
                    } else {
                        andArr.push(filters[i-1]);
                    }
                    filters.splice(i - 1, 1);
                } else {
                    filters.splice(i - 1, 2, {'$and': [filters[i-1], filters[i]]});
                }
            } else {
                prevIsAnd = false;
            }
        }
        if (filters.length > 1) {
            return {'$or': filters};     // or obj
        }
        else {return filters[0];}  // and obj
    }
}
// Collect fields and values
collectFilterParams = () => {
    currReq.filters = [], currReq.qfilters = [], currReq.operands = [], currReq.brackets = [];
    $('.paramPair').each((index, e) => {
        var op = $(e).find('.filterOperand').text();
        var label = $(e).find('.fieldLabel').text().toLowerCase();
        var value = $(e).find('.fieldValue').text();    // For query preview on client side
        var qvalue = value;                             // For forming backend queries
        var classlists = e.classList;
        var inBracket1 = classlists.contains('bracket-1');
        var inBracket2 = classlists.contains('bracket-2');
        var inBracket3 = classlists.contains('bracket-3');

        if (label.startsWith('canopy')) {
            label = 'canopy_condition';
            qvalue = value.toLowerCase();
        };
        // Read checked quality values correctly
        if (label == 'quality') {
            value = [], qvalue = [];
            for (let i = 0; i < 5; i++) {
                let checkbox = $(e).find('.qualityCheckInput')[i];
                if (checkbox.checked) {
                    value.push(parseInt(checkbox.value));
                    qvalue.push({'properties.data.quality': parseInt(checkbox.value)});
                }
            }
            qvalue = {'$or': qvalue};
        }
        // Read ranged values correctly
        if (['dbh', 'height', 'crowndia.'].includes(label)) {
            let lb = $(e).find('.rangeInput')[0].value == '' ? 0 : $(e).find('.rangeInput')[0].value,
                gb = $(e).find('.rangeInput')[1].value == '' ? 10000 : $(e).find('.rangeInput')[1].value;
            value = lb + '-' + gb;
            qvalue = {'$lt': parseFloat(gb), '$gt': parseFloat(lb)};
        }
        
        let obj = {};
        obj[filterKeys[label]] = qvalue;
        currReq.filters.push(label + ':' + value);
        if (label == 'quality') { currReq.qfilters.push(qvalue); } 
        else { currReq.qfilters.push(obj); }
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
        filters[i] = JSON.stringify(filters[i]);
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
// Post request for querying
queryBackend = (elemMatch, previewLimit, nthEntrySet, renderMarkers, turnPage, bounds = null) => {
    var deferred = new $.Deferred();
    $.post('/search/wssearch', {"query": JSON.stringify(currReq.backendQ), "elemMatch": elemMatch, "limit": previewLimit, 
        "nthEntrySet": nthEntrySet, "getCoords": renderMarkers})
        .done(data => {
            var trees = data['res_preview'];
            var coords = data['res_coords'];
            var numRes = data['num_res'];
            currReq.url = '/search/wssearch';
            // Clear previous results
            $('#jsonViewerContainer').empty(); 
            $('#treeTabs').empty();
            // Show number of results
            $('#numRes').html(numRes);
            $('#numResContainer').show();
            currNumRes = numRes;
            // Show json code snippets if trees found
            if (numRes != 0) {
                $('#dlButtons').show();
                $('#dlButtons').find('*').show();
                $('#mapContainer').show();
                // Update for output
                jsonOutput = JSON.stringify(trees[0], null, 2);
                $('.treeTab').removeClass('active');
                // Show json data of the given preview number of trees
                if (nthEntrySet > 0) {
                    $('#treeTabs').append('<li class="page-item nav-item"><a class="page-link nav-link" onclick="prevPageSet()" aria-label="Next"><span aria-hidden="true">&laquo;</span></a></li>');
                }
                for (let i = 0; i < Math.min(previewLimit, numRes - previewLimit*nthEntrySet); i++) {
                    var idx = i+nthEntrySet*previewLimit;
                    // Show tabs
                    $('#treeTabs').css('display', 'flex');
                    $('#treeTabs').append('<li id="treeTab'+ idx +'" class="page-item nav-item"><a class="page-link nav-link treeTab" onclick="toggleTab(this)">'+(idx+1)+'</a></li>');
                    $('#treeTab' + idx).show();
                    // Load data into html
                    $('#jsonViewerContainer').append('<pre class="previewTree" id="tree-' + idx + '"></pre>');
                    $('#tree-' + idx).jsonViewer(trees[i]);
                    previewTrees.push(JSON.stringify(trees[i], null, 2));
                    // Show only one code block
                    if (i > 0) {
                        $('#tree-' + idx).hide();
                    }
                }
                // Add "Next" for pagination
                if (numRes - previewLimit*(nthEntrySet+1) > 0) {
                    $('#treeTabs').append('<li class="page-item nav-item"><a class="page-link nav-link" onclick="nextPageSet()" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>');
                }
                $('#treeTab' + nthEntrySet*previewLimit).children().addClass('active');

                // Draw map 
                if (renderMarkers) {
                    drawMap(coords, bounds);
                } else if (!renderMarkers && !turnPage) {
                    cleanMap();
                    ready = false;
                }
            }
            // If no trees satisfy the query, clear prev results
            else {
                $('#treeTabs').hide();
                $('#dlButtons').hide();
                cleanMap();
                $('#mapContainer').hide();
            }
            // Show alert when max number of markers exceeded, 
            // no marker will be displayed in order to avoid browser crashes
            if (renderMarkers && !coords) {
                alert("There are too many results. The markers won't be displayed now for performance reasons.");
            }
            
            deferred.resolve(numRes);
        })
        .fail((xhr, status, error) => {
            console.log(xhr);
            console.log(status);
            console.log(error);
        });
    return deferred.promise();
}
// Next set of trees for pagination
nextPageSet = () => { 
    var renderMarkers = $('#markerRenderCheckbox')[0].checked;
    var bounds = map.getBounds();
    nthEntrySet += 1;
    queryBackend(elemMatch, previewLimit, nthEntrySet, renderMarkers, true, bounds);
}
// Previous set of trees for pagination
prevPageSet = () => {
    var renderMarkers = $('#markerRenderCheckbox')[0].checked;
    var bounds = map.getBounds();
    nthEntrySet -= 1;
    queryBackend(elemMatch, previewLimit, nthEntrySet, renderMarkers, true, bounds);
}
// Apply geometric bounding box restriction to the existing results
geoSearch = () => {
    var bounds = map.getBounds();
    var latlngObj = snapLatLngToBound(map.getBounds());
    var geom = {    "type": "Polygon", "coordinates": [[
                    [latlngObj._northEast.lng, latlngObj._northEast.lat],
                    [latlngObj._southWest.lng, latlngObj._northEast.lat],
                    [latlngObj._southWest.lng, latlngObj._southWest.lat],
                    [latlngObj._northEast.lng, latlngObj._southWest.lat],
                    [latlngObj._northEast.lng, latlngObj._northEast.lat],
                ]],
                    "crs": {
                        "type": "name",
                        "properties": { "name": "urn:x-mongodb:crs:strictwinding:EPSG:4326" }
                    }
                };
    currReq.backendQ["geometry"] = {"$geoWithin": {"$geometry": geom}};
    let renderMarkers = $('#markerRenderCheckbox')[0].checked;
    queryBackend(elemMatch, previewLimit, nthEntrySet, renderMarkers, false, bounds);
    // Update interface to show the number of results correctly
    $('.normRes').hide();
    $('.geoRes').show();
    $('#prevNumRes').html(prevNumRes);
}
// Clear geometric selection (display the full search results again)
clearGeoSelection = () => {
    let renderMarkers = $('#markerRenderCheckbox')[0].checked;
    var bounds = map.getBounds();
    delete currReq.backendQ["geometry"];
    queryBackend(elemMatch, previewLimit, nthEntrySet, renderMarkers, false, bounds);
    // Update interface to show the number of results correctly
    $('.geoRes').hide();
    $('.normRes').show();
    prevNumRes = null;
}

// Copy the query in preview to clipboard
// Referenced source: https://www.codegrepper.com/code-examples/javascript/copy+text+to+clipboard+javascript
genPermalink = () => {
    collectFilterParams();
    let query = btoa(JSON.stringify(constrQueryExp()));
    let targetText = window.location.protocol + '//' + window.location.host + '/query/' + query;
    if (!navigator.clipboard){ // use old commandExec() way
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val(targetText).select();
        document.execCommand("copy");
        $temp.remove();
    } else{
        navigator.clipboard.writeText(targetText);
    }    
    alert('Link for the current query is successfully copied to your clipboard.');
}
// Export query for future use
exportQuery = () => {
    updateQueryPreview();
    if (currReq.backendQ == '') {
        let filters = currReq.filters, operands = currReq.operands, brackets = currReq.brackets;
        currReq.backendQ = processAND(0, currReq.filters.length - 1, filters, operands, brackets, elemMatch);
    };
    
    var queryJsonExp = constrQueryExp();
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
        if (lab === 'Mode' || lab === 'Source') {val = val.toUpperCase();}
        if (lab.startsWith('Canopy')) {lab = 'Canopy';}
        if (lab === 'Dbh') {lab = 'DBH';}
        // Add filter to page
        addSearchFilter({'text': lab});
        // Show the value of filter
        if (lab === 'Quality') {
            let checkedVals = val.split(',');
            for (let i = 0; i < checkedVals.length; i++) {
                let n = parseInt(checkedVals[i]) - 1;
                $('.fieldValue:last').find('.qualityCheckInput')[n].checked = true;
            }
        } else if (['DBH', 'Height', 'CrownDia.'].includes(lab)) {
            let range = val.split('-');
            $('.fieldValue:last').find('.rangeInput')[0].value = range[0];
            $('.fieldValue:last').find('.rangeInput')[1].value = range[1];
        } else {
            $('.fieldValue:last').html(val).attr('style', 'color: #212529');
        }
        // Set the operand
        if (query.operands[i] == 'OR') {toggleOp($('.filterOperand:last'));}
        // Add brackets
        for (let depth = 1; depth <= query.brackets[i]; depth++) {
            moveRight($('.rightArrow:last')[0]);
        }
    }
    // Update query preview
    $('#queryPreviewArea').text(query.previewString); 
    // Update checkboxes etc.
    $('#elemMatchCheckbox').prop('checked', query.elemMatch);
    $('#markerRenderCheckbox').prop('checked', query.renderMarkers);
    $('#numPreviewTrees').val(query.previewLimit);
}   
// Clean search
cleanSearchBar = () => {
    $('.paramPair').remove();
    $('#queryPreviewArea').text('Your query: ');
}
// Construct current query in object format for exportation
constrQueryExp = () => {
    queryExp = {
        "backendQuery": currReq.backendQ,
        "filters": currReq.filters,
        "operands": currReq.operands,
        "brackets": currReq.brackets,
        "previewString": currReq.stringFormat,
        "elemMatch": $('#elemMatchCheckbox')[0].checked,
        "previewLimit": Math.min($('#numPreviewTrees').val(), maxPreviewLimit),
        "renderMarkers": $('#markerRenderCheckbox')[0].checked,
    };
    return queryExp;
}

// Utility function: generate a download link according to the current query and get requested info from backend
// Source: https://stackoverflow.com/questions/283956/is-there-any-way-to-specify-a-suggested-filename-when-using-data-uri
saveContent = (fileName, url) => {
    var link = document.createElement('a');
    link.download = fileName;
    link.href = url + btoa(JSON.stringify(currReq.backendQ));
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
    saveContent('res_feature_collection.json', '/download/exportcollection/');
}
// Save all results into zipped csv-files
saveCSV = () => {
    saveContent('csv.zip', '/download/exportcsv/');
}
// Save point clouds of all results into a zip
// The JSZip library: https://github.com/Stuk/jszip
savePointClouds = () => {
    if (currReq.url.startsWith('/getitem')) {
        var getReqUrl = '/download/lazlinks/tree/' + currReq.url.split('/')[2];
    } else {
        getReqUrl = '/download/lazlinks/' + btoa(JSON.stringify(currReq.backendQ));
    }
    $.get(getReqUrl, data => {
        pcUrls = data['links'];
        // If the response exceed threshold, enable bulk-download instead of zipping point clouds
        if (pcUrls.length >= lazDlLimit) {
            $('#modalBtn').click();
            var link = $('#pcUrlListLink')[0];
            link.download = 'urls.txt';
            link.href = 'data:,' + pcUrls;
            return;
        }
        // For fewer data, provide a zip file of the point clouds for users to download
        var zip = new JSZip();
        var cntFilesDownloaded = 0;
        // Show progress bar if request successful
        $('#downLoadProgressSection').show();
        // Iterate through the list of urls
        pcUrls.forEach((url, idx, array) => {
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
                    // Create the zip file for download
                    zip.generateAsync({type : "blob", compression : "DEFLATE"})
                        .then(content => {
                            var link = document.createElement('a');
                            link.download = 'pointclouds';
                            link.href = URL.createObjectURL(content);
                            link.click();
                            // Hide progress bar and reset 
                            $('#downLoadProgressSection').hide();
                            $('#pcState').html('Preparing Point Clouds on server... <span id="dlState"></span>');
                            $('#progressBar').attr('aria-valuenow', 0).css('width', '0%');
                            cntFilesDownloaded = 0
                    });
                }
            })
        });
    });
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
    var rangeFilterFVSnippet = 
        '<div class="fvWrapper" style="display: inline-block; width: calc(100% - 4rem);">' + 
            '<span class="fieldLabel ' + field + '">' + field + '</span>' + 
            '<div class="btn-light fieldValue" style="display: inline-block; color: #606060">' +
                '<input type="text" class="rangeInput"><span class="mx-2px">-</span><input type="text" class="rangeInput">' + 
            '</div>'+
        '</div>';
    
    if ($('[id^="paramPair"]').length == 0) {  // If no filter exists yet
        // Insert the first filter
        if (field === 'Quality') {
            $('.addFilter:first').before(addWholeFilterSnippet(qualityFilterFVSnippet, newFilterID, andOp));  
        } else if (field === 'DBH' || field === 'Height' || field === 'CrownDia.') {
            $('.addFilter:first').before(addWholeFilterSnippet(rangeFilterFVSnippet, newFilterID, andOp));
        } else {
            $('.addFilter:first').before(addWholeFilterSnippet(normalFilterFVSnippet, newFilterID, andOp));
            // Update available values in the dropdown according to the added field filter
            updateAvailableVals(newFilterID, field);
        }
        $('.filterOperand:first').text('.').removeClass('andOp').removeClass('orOp').addClass('firstFilter');
    } else {  // Otherwise insert code after the last filter, and add connecting operand
        if (field === 'Quality') {
            $('[id^="paramPair"]:last').after(addWholeFilterSnippet(qualityFilterFVSnippet, newFilterID, andOp));
        } else if (field === 'DBH' || field === 'Height' || field === 'CrownDia.') {
            $('[id^="paramPair"]:last').after(addWholeFilterSnippet(rangeFilterFVSnippet, newFilterID, andOp));
        } else {
            $('[id^="paramPair"]:last').after(addWholeFilterSnippet(normalFilterFVSnippet, newFilterID, andOp));
            updateAvailableVals(newFilterID, field);
        }
    }
    
}
// Remove filter
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
            $(availableValuesEl).append('<li><input type="text" placeholder="Search.." id="filterSearchInput" onkeyup="filterSearch(this)"></li>');
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
        case "Source":
            var sources = ['TLS', 'ALS', 'ULS', 'FI'];
            sources.forEach(source => {
                $(availableValuesEl).append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + source + '</a></li>'
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
// Search inside a filter (e.g. species that corresponds to input)
// Source: https://www.w3schools.com/howto/tryit.asp?filename=tryhow_css_js_dropdown_filter
filterSearch = input => {
    var text = input.value.toUpperCase();
    var ul = input.parentElement.parentElement
    var a = ul.getElementsByTagName("a");
    for (i = 0; i < a.length; i++) {
        txtValue = a[i].textContent || a[i].innerText;
        if (txtValue.toUpperCase().indexOf(text) > -1) {
        a[i].style.display = "";
        } else {
        a[i].style.display = "none";
        }
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
// Snap lat/lng to bounds
snapLatLngToBound = latlngObj => {
    if (latlngObj._northEast.lng > 180) {latlngObj._northEast.lng = 180;}
    if (latlngObj._southWest.lng > 180) {latlngObj._southWest.lng = 180;}
    if (latlngObj._northEast.lng < -180) {latlngObj._northEast.lng = -180;}
    if (latlngObj._southWest.lng < -180) {latlngObj._southWest.lng = -180;}
    if (latlngObj._northEast.lat > 90) {latlngObj._northEast.lat = 90;}
    if (latlngObj._southWest.lat > 90) {latlngObj._southWest.lat = 90;}
    if (latlngObj._northEast.lat < -90) {latlngObj._northEast.lat = -90;}
    if (latlngObj._southWest.lat < -90) {latlngObj._southWest.lat = -90;}
    return latlngObj;
}

//////////////////////////////////////////////////////////////////////////
//  Leaflet                                                             //
//////////////////////////////////////////////////////////////////////////
// Leaflet Draw API: https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html
// Referencing supercluster sample code: https://stackoverflow.com/questions/51033188/how-to-use-supercluster 
// Supercluster library: https://github.com/mapbox/supercluster 

// Set up the tile layer
L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Data © <a href="http://osm.org/copyright">OpenStreetMap</a>',
    maxNativeZoom: 19,
    maxZoom: 22
}).addTo(map);

// Init geoJSONLayer(group)
var markers = L.geoJSON(null, {
        pointToLayer: createClusterIcon
}).addTo(map);
// Set zooming bounds of clusters (avoid zooming in too far)
markers.on('clusterclick', function (a) {
    map.fitBounds(a.layer.getBounds().pad(0.3)); 
});

function createClusterIcon(feature, latlng) {
    if (!feature.properties.cluster) {
        return L.marker(latlng).bindPopup('<a target="_blank" href="/getitem/' + feature._id_x + '">' + feature.properties.id + '</a>');
    }
  
    var count = feature.properties.point_count;
    var size =
      count < 100 ? 'small' :
      count < 1000 ? 'medium' : 'large';
    var icon = L.divIcon({
      html: '<div><span>' + feature.properties.point_count_abbreviated + '</span></div>',
      className: 'marker-cluster marker-cluster-' + size,
      iconSize: L.point(40, 40)
    });
  
    return L.marker(latlng, {
      icon: icon
    });
}

function update() {
    if (!ready) return;
    var bounds = map.getBounds();
    var bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()];
    var zoom = map.getZoom();
    var clusters = index.getClusters(bbox, zoom);
    markers.clearLayers();
    markers.addData(clusters);
}

// Update the displayed clusters after panning/zooming
map.on('moveend', update);

// Zoom to expand the cluster clicked
markers.on('click', function(e) {
    var clusterId = e.layer.feature.properties.cluster_id;
    var center = e.latlng;
    var expansionZoom;
    if (clusterId) {
      expansionZoom = index.getClusterExpansionZoom(clusterId);
      map.flyTo(center, expansionZoom, {duration: 0.5});
    }
});


// Show resulting trees on the map
drawMap = (trees, bounds = null) => {
    
    map.invalidateSize();  // Make sure tiles render correctly
    markers.clearLayers();
    if (bounds) {
        map.fitBounds(bounds); // Fit to previous geo bound            
    } else {
        map.setView([0, 0], 0); // World view
        setTimeout(() => {
            let center = markers.getLayers()[0]._latlng;
            map.flyTo(center, 3, {duration: 0.01});
        }, 300);
    }
    // Initialize the supercluster index.
    index = new Supercluster({
        radius: 60,
        extent: 256,
        maxZoom: 18
    }).load(trees); // Load geojson features
    ready = true;
    update();

}

// Clean map, remove all markers and layers
cleanMap = () => {
    map.invalidateSize();  // Make sure tiles render correctly
    markers.clearLayers();  // Remove previous markers
}

