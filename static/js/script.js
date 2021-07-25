var species, n_trees, jsonOutput, currReq, getEverySec;

window.onload = () => {
    // Load stats on start
    $.get('/stats', (data) => {
        n_trees = data['n_trees'];
        $('#numTrees').html(n_trees);
        $('#numSpecies').html(data['n_species']);
        $('#nTrees').html(n_trees-1);
    });

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
        $.get('/getitem?index=' + idx, data => {
            currReq = '/getitem?index=' + idx;
            var jsonStr = data['item'];
            // Update jsonOutput
            jsonOutput = jsonStr;
            var jsonObj = JSON.parse(jsonStr);
            // Clear previous results
            $('#jsonViewerContainer').empty();
            // Write new result
            $('#jsonViewerContainer').html('<pre id="idSearchRes"></pre>');
            $('#idSearchRes').jsonViewer(jsonObj, {rootCollapsable: false, withLinks: false});
        });
        $('#numResContainer').hide();
        $('#treeTabs').hide();
        $('#saveAllButton').hide();
        $('#savePointCButton').hide();
        $('#jsonSnippetSection').css('padding-bottom', '2rem').show();
        $('html,body').animate({
            scrollTop: $('#jsonSnippetSection').offset().top},
            'slow');
    }
}

// Query trees via property and value
searchDB = () => {
    var property = $('#searchField').text().toLowerCase();
    var value = $('#fieldValue').text();
    if (property == 'canopy condition') {
        property = 'canopy_condition';
    } else if (property == 'quality') {
        if (!checkQBounds()) {
            return;
        }
        value = $('#qualityFrom').text() + ',' + $('#qualityTo').text();
    }
    // Do get
    if (property != '' && property != 'select search field' 
        && value != '' && value != 'Please select a field first'
        && value != 'Choose a value') {
        $.get('/trees?field=' + property + '&value=' + value, data => {
            currReq = '/trees?field=' + property + '&value=' + value;
            var trees = data['query'];
            var num;
            // Clear previous results
            $('#jsonViewerContainer').empty(); 
            // Show number of results
            $('#numRes').html(trees.length);
            // Show json code snippets if trees found
            if (trees.length != 0) {
                $('#numResContainer').show();
                $('#saveAllButton').show();
                $('#savePointCButton').show();
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
                    // Show only one code block
                    if (i > 0) {
                        $('#tree-' + i).hide();
                    }
                }
                $('#treeTab0').children().addClass('active');
            }
        });
        $('#jsonSnippetSection').css('padding-bottom', '7rem').show();
        $('html,body').animate({
            scrollTop: $('#jsonSnippetSection').offset().top},
            'slow');
        
        // dummy partial implementation Point Clouds download
        if (value == 'Pinus sylvestris') {
            $('#savePointCButton').removeAttr('disabled');
        } else {
            $('#savePointCButton').attr('disabled', 'disabled');
        }

    } else {
        $("#results").html(""); // empty list
    }
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
    $.get(currReq, data => {
        outString += JSON.stringify(data['query']) + '}';
        saveContent(outString, 'res_feature_collection.json');
    })
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

// After selecting a field, the available values will be updated in the second dropdown
searchFieldSelected = e => {
    $('#searchField').html(e.text);
    $('#searchField').attr('style', 'color: #000');
    $('#fieldValue').html('Choose a value');
    $('#fieldValue').attr('style', 'color: #aaa');
    $('#availableValues').empty();
    switch (e.text) {
        case "Species":
            $('#normalValUI').show();
            $('#qualityUI').hide();
            $.get('/listspecies', data => {
                data["species"].sort().forEach(specie => {
                    $('#availableValues').append(
                        '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + specie + '</a></li>'
                    );
                });
            })
            break;
        case "Mode":
            $('#normalValUI').show();
            $('#qualityUI').hide(); 
            var modes = ['TLS', 'ALS', 'ULS'];
            modes.forEach(mode => {
                $('#availableValues').append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + mode + '</a></li>'
                );
            })
            break;
        case "Canopy Condition":
            $('#normalValUI').show();
            $('#qualityUI').hide();
            var canopy_conditions = ['leaf-on', 'leaf-off'];
            canopy_conditions.forEach(cond => {
                $('#availableValues').append(
                    '<li><a class="dropdown-item" onclick="fieldValueSelected(this)">' + cond + '</a></li>'
                );
            })
            break;
        case "Quality":
            $('#normalValUI').hide();
            $('#qualityUI').show();
            break;
        default:
            break;
    }
}

// Update dropdown text when users selects a value
fieldValueSelected = e => {
    $('#fieldValue').html(e.text).attr('style', 'color: #000');
}
qualityFrom = e => {
    $('#qualityFrom').html(e.text).attr('style', 'color: #000');
    checkQBounds();
}
qualityTo = e => {
    $('#qualityTo').html(e.text).attr('style', 'color: #000');
    checkQBounds();
}
// Check if the quality lower bound is greater than upper bound 
checkQBounds = () => {
    if ($('#qualityFrom').text() > $('#qualityTo').text()) {
        $('#qualityFrom').addClass('warning');
        $('#qualityTo').addClass('warning');
        $('#qErr').show();
        return false;
    } else {
        $('#qualityFrom').removeClass('warning');
        $('#qualityTo').removeClass('warning');
        $('#qErr').hide();
        return true;
    }
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