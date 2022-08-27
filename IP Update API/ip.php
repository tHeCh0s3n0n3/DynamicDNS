<?php

// ini_set('display_errors', 1);
// ini_set('display_startup_errors', 1);
// error_reporting(E_ALL);

if(isset($_GET['action'])) {
    require_once("AuthKey.inc.php");
    global $AuthKey;

    $token = GetAuthToken();
    if (null == $token || $token !== $AuthKey) {
        http_response_code(401);
        die();
    }

    switch ($_GET['action']) {
        case "update":
            ProcessUpdate();
            break;
        case "getAll":
            ProcessGetAll();
            break;
        case "auto-update": // Service-side update
            ProcessServerSideUpdate();
            break;
        default:
            die();
    }
}

function ProcessUpdate() {
    UpdateIP($_POST['subdomain'], $_POST['ip']);
}

function ProcessGetAll() {
    require_once("SQLiteConnection.inc.php");
    $pdo = (new SQLiteConnection())->connect();
    if (null == $pdo) {
        echo 'Whoops, could not connect to the SQLite database!';
        http_response_code(500);
        die();
    }

    $sth = $pdo->prepare("SELECT * FROM Subdomains");
    $sth->execute();
    $result = $sth->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode($result);
    exit();
}

function ProcessServerSideUpdate() {
    // Get the IP of the calling client
    $ip = $_SERVER['REMOTE_ADDR'];
    if (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
    }

    UpdateIP($_GET['subdomain'], $ip);
}

function UpdateIP($subdomain, $ip) {
    $response = new stdClass();

    $response->subdomain = $subdomain;
    $response->ip = $ip;

    require_once("SQLiteConnection.inc.php");
    $pdo = (new SQLiteConnection())->connect();
    if (null == $pdo) {
        echo 'Whoops, could not connect to the SQLite database!';
        http_response_code(500);
        die();
    }

    $sth = $pdo->prepare("SELECT * FROM Subdomains WHERE subdomain = :subdomain");
    $sth->bindParam(":subdomain", $subdomain);
    $sth->execute();
    $result = $sth->fetch(PDO::FETCH_ASSOC);

    $query = "";
    if (false !== $result) {
        if($result['ip'] == $ip) {
            // No updated needed.
            http_response_code(304);
            exit();
        }
        $query = "UPDATE Subdomains SET ip = :ip WHERE subdomain = :subdomain";
    } else {
        $query = "INSERT INTO Subdomains (subdomain, ip) VALUES (:subdomain, :ip)";
    }

    $sth2 = $pdo->prepare($query);
    $sth2->bindParam(":ip", $ip);
    $sth2->bindParam(":subdomain", $subdomain);
    $sth2->execute();
    http_response_code(201);
    $response->result = 201;
    echo json_encode($response);
}

/**
 * Get header Authorization
 * */
function getAuthorizationHeader(){
    $headers = null;
    if (isset($_SERVER['Authorization'])) {
        $headers = trim($_SERVER["Authorization"]);
    }
    else if (isset($_SERVER['HTTP_AUTHORIZATION'])) { //Nginx or fast CGI
        $headers = trim($_SERVER["HTTP_AUTHORIZATION"]);
    } elseif (function_exists('apache_request_headers')) {
        $requestHeaders = apache_request_headers();
        // Server-side fix for bug in old Android versions (a nice side-effect of this fix means we don't care about capitalization for Authorization)
        $requestHeaders = array_combine(array_map('ucwords', array_keys($requestHeaders)), array_values($requestHeaders));
        //print_r($requestHeaders);
        if (isset($requestHeaders['Authorization'])) {
            $headers = trim($requestHeaders['Authorization']);
        }
    }
    return $headers;
}
/**
* get access token from header
* */
function GetAuthToken($type = "Basic") {
    $headers = getAuthorizationHeader();
    // HEADER: Get the access token from the header
    if (!empty($headers)) {
        if (preg_match('/' . $type . '\s(\S+)/', $headers, $matches)) {
            return $matches[1];
        }
    }
    return null;
}