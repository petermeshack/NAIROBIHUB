package com.example.nairobihub

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.media.RingtoneManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.security.SecureRandom
import java.security.cert.X509Certificate
import java.util.concurrent.TimeUnit
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager
import kotlin.random.Random

// High-contrast legible color palettes
val DarkBackground = Color(0xFF0B130F)
val LightBackground = Color(0xFFF0F5F2)
val CardBackground = Color(0xFF132219)
val LightCardBackground = Color(0xFFFFFFFF)
val BorderColor = Color(0xFF1E3A29)
val LightBorderColor = Color(0xFFD1D5DB)
val AccentGreen = Color(0xFF00B050)
val TextPrimary = Color(0xFFFFFFFF)
val LightTextPrimary = Color(0xFF111827)
val TextSecondary = Color(0xFFD1D5DB)
val LightTextSecondary = Color(0xFF4B5563)
val StatusRed = Color(0xFFEF4444)
val StatusGreen = Color(0xFF22C55E)

fun parseHexColor(colorStr: String, defaultColor: Color): Color {
    return try {
        Color(android.graphics.Color.parseColor(if (colorStr.startsWith("#")) colorStr else "#$colorStr"))
    } catch (_: Exception) {
        defaultColor
    }
}

fun getFontScaleMultiplier(scaleSetting: String): Float {
    return when (scaleSetting) {
        "Small" -> 0.85f
        "Large" -> 1.15f
        "Custom" -> 1.25f
        else -> 1.0f // Medium
    }
}

/**
 * Central notification handler that controls all Toast banners and phone sound alerts
 * according to user preferences configured in Settings.
 */
fun showNotificationToast(context: android.content.Context, dbHelper: DatabaseHelper, message: String, eventCategory: String = "All System Events") {
    val soundAlerts = dbHelper.getSetting("notif_sound", "On") == "On"
    val bannerAlerts = dbHelper.getSetting("notif_banner", "On") == "On"
    val configuredFilter = dbHelper.getSetting("notif_filter", "All System Events")

    val shouldShow = when (configuredFilter) {
        "Errors & Warnings Only" -> eventCategory.contains("Error", true) || eventCategory.contains("Warning", true)
        "Connection State Changes Only" -> eventCategory.contains("Connection", true) || eventCategory.contains("Space", true)
        else -> true
    }

    if (shouldShow) {
        if (soundAlerts) {
            try {
                val notificationUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
                val ringtone = RingtoneManager.getRingtone(context, notificationUri)
                ringtone?.play()
            } catch (_: Exception) {}
        }

        if (bannerAlerts) {
            Toast.makeText(context, if (soundAlerts) "🔔 [Audio] $message" else message, Toast.LENGTH_SHORT).show()
        }
    }
}

fun createUnsafeOkHttpClient(): OkHttpClient {
    return try {
        val trustAllCerts = arrayOf<TrustManager>(object : X509TrustManager {
            override fun checkClientTrusted(chain: Array<out X509Certificate>?, authType: String?) {}
            override fun checkServerTrusted(chain: Array<out X509Certificate>?, authType: String?) {}
            override fun getAcceptedIssuers(): Array<X509Certificate> = arrayOf()
        })
        val sslContext = SSLContext.getInstance("SSL")
        sslContext.init(null, trustAllCerts, SecureRandom())
        val sslSocketFactory = sslContext.socketFactory

        OkHttpClient.Builder()
            .sslSocketFactory(sslSocketFactory, trustAllCerts[0] as X509TrustManager)
            .hostnameVerifier { _, _ -> true }
            .connectTimeout(8, TimeUnit.SECONDS)
            .readTimeout(8, TimeUnit.SECONDS)
            .build()
    } catch (_: Exception) {
        OkHttpClient.Builder()
            .connectTimeout(8, TimeUnit.SECONDS)
            .readTimeout(8, TimeUnit.SECONDS)
            .build()
    }
}

fun getItemIcon(itemType: String): ImageVector {
    return when (itemType.lowercase().trim()) {
        "folder" -> Icons.Default.Folder
        "image", "photo" -> Icons.Default.Image
        "video", "movie" -> Icons.Default.VideoLibrary
        "audio", "music" -> Icons.Default.AudioFile
        "word", "excel", "powerpoint", "txt document", "document", "pdf", "text" -> Icons.Default.Description
        else -> Icons.Default.InsertDriveFile
    }
}

class MainActivity : ComponentActivity() {
    private lateinit var dbHelper: DatabaseHelper
    private val client = createUnsafeOkHttpClient()

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val granted = permissions.entries.all { it.value }
        if (granted) {
            Toast.makeText(this, "Storage permissions granted!", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(this, "Storage permissions denied. Some sync features may be restricted.", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        dbHelper = DatabaseHelper(this)

        checkAndRequestPermissions()

        setContent {
            var currentTheme by remember { mutableStateOf(dbHelper.getSetting("theme", "Dark Mode")) }
            var highContrast by remember { mutableStateOf(dbHelper.getSetting("high_contrast", "Off") == "On") }
            var accentColorHex by remember { mutableStateOf(dbHelper.getSetting("accent_color", "#00B050")) }
            var defaultViewSetting by remember { mutableStateOf(dbHelper.getSetting("default_view", "Dashboard")) }

            val initialTab = when (defaultViewSetting) {
                "My Device" -> 1
                "Settings" -> 2
                else -> 0
            }

            NairobiHubAppTheme(theme = currentTheme, highContrast = highContrast, accentColorHex = accentColorHex) {
                var servers by remember { mutableStateOf(dbHelper.getConnectedServers()) }
                var remoteFiles by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
                var activityLogs by remember { mutableStateOf(listOf("Client initialized successfully.")) }

                MainScreen(
                    dbHelper = dbHelper,
                    client = client,
                    servers = servers,
                    onServersChanged = { servers = it },
                    remoteFiles = remoteFiles,
                    onRemoteFilesChanged = { remoteFiles = it },
                    activityLogs = activityLogs,
                    onLogAdded = { log -> activityLogs = listOf(log) + activityLogs },
                    initialTab = initialTab,
                    onSettingsUpdated = {
                        currentTheme = dbHelper.getSetting("theme", "Dark Mode")
                        highContrast = dbHelper.getSetting("high_contrast", "Off") == "On"
                        accentColorHex = dbHelper.getSetting("accent_color", "#00B050")
                    }
                )
            }
        }
    }

    private fun checkAndRequestPermissions() {
        val permissionsToRequest = mutableListOf<String>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_IMAGES) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.READ_MEDIA_IMAGES)
            }
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_VIDEO) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.READ_MEDIA_VIDEO)
            }
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.READ_MEDIA_AUDIO)
            }
        } else {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.READ_EXTERNAL_STORAGE)
            }
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
            }
        }

        if (permissionsToRequest.isNotEmpty()) {
            requestPermissionLauncher.launch(permissionsToRequest.toTypedArray())
        }
    }
}

@Composable
fun NairobiHubAppTheme(theme: String, highContrast: Boolean, accentColorHex: String, content: @Composable () -> Unit) {
    val isDark = theme == "Dark Mode"
    val bg = if (isDark) DarkBackground else LightBackground
    val surface = if (isDark) CardBackground else LightCardBackground
    val primary = if (highContrast) Color(0xFFFFCC00) else parseHexColor(accentColorHex, AccentGreen)
    val onBg = if (isDark) TextPrimary else LightTextPrimary

    val colorScheme = if (isDark) {
        darkColorScheme(
            background = bg,
            surface = surface,
            primary = primary,
            onPrimary = Color.White,
            onBackground = onBg,
            onSurface = onBg
        )
    } else {
        lightColorScheme(
            background = bg,
            surface = surface,
            primary = primary,
            onPrimary = Color.White,
            onBackground = onBg,
            onSurface = onBg
        )
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    dbHelper: DatabaseHelper,
    client: OkHttpClient,
    servers: List<Map<String, String>>,
    onServersChanged: (List<Map<String, String>>) -> Unit,
    remoteFiles: List<JSONObject>,
    onRemoteFilesChanged: (List<JSONObject>) -> Unit,
    activityLogs: List<String>,
    onLogAdded: (String) -> Unit,
    initialTab: Int,
    onSettingsUpdated: () -> Unit
) {
    var selectedTab by remember { mutableStateOf(initialTab) }
    val tabs = listOf("Dashboard", "My Device", "Settings")
    val icons = listOf(Icons.Default.Home, Icons.Default.Phone, Icons.Default.Settings)
    val theme = dbHelper.getSetting("theme", "Dark Mode")
    val isDark = theme == "Dark Mode"
    val fontScale = getFontScaleMultiplier(dbHelper.getSetting("font_scale", "Medium"))

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                        Text(
                            "Nairobi County DES File Hub",
                            fontWeight = FontWeight.Bold,
                            fontSize = (20 * fontScale).sp,
                            color = if (isDark) TextPrimary else LightTextPrimary
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = if (isDark) CardBackground else LightCardBackground)
            )
        },

        bottomBar = {
            NavigationBar(containerColor = if (isDark) CardBackground else LightCardBackground) {
                tabs.forEachIndexed { index, title ->
                    NavigationBarItem(
                        icon = { Icon(icons[index], contentDescription = title) },
                        label = { Text(title, fontSize = (10 * fontScale).sp, color = if (isDark) TextPrimary else LightTextPrimary) },
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = Color.White,
                            selectedTextColor = MaterialTheme.colorScheme.primary,
                            unselectedIconColor = if (isDark) TextSecondary else LightTextSecondary,
                            unselectedTextColor = if (isDark) TextSecondary else LightTextSecondary,
                            indicatorColor = MaterialTheme.colorScheme.primary
                        )
                    )
                }
            }
        }
    ) { innerPadding ->
        Box(modifier = Modifier.padding(innerPadding).fillMaxSize().background(if (isDark) DarkBackground else LightBackground)) {
            when (selectedTab) {
                0 -> DashboardSection(dbHelper, client, servers)
                1 -> MyDeviceSection(dbHelper, client, dbHelper, servers, onServersChanged, remoteFiles, onRemoteFilesChanged, onLogAdded)
                2 -> SettingsSection(dbHelper, activityLogs, onLogAdded, onSettingsUpdated)
            }
        }
    }
}

fun ensureValidSession(client: OkHttpClient, dbHelper: DatabaseHelper, srv: Map<String, String>, clientId: String): String {
    var token = srv["session_token"] ?: ""
    val url = srv["url"] ?: ""
    val key = srv["server_key"] ?: ""
    if (token.isNotEmpty()) return token

    try {
        val body = JSONObject().put("username", dbHelper.getClientInfo().second).toString()
        val reqBuilder = Request.Builder()
            .url("$url/api/auth/connect")
            .header("X-Client-ID", clientId)
            .header("bypass-tunnel-reminder", "true")
            .header("User-Agent", "NairobiHubClient/1.0")

        if (key.isNotEmpty()) {
            reqBuilder.header("X-Server-Key", key)
        }

        val resp = client.newCall(reqBuilder.post(body.toRequestBody("application/json".toMediaType())).build()).execute()
        if (resp.isSuccessful) {
            val json = JSONObject(resp.body?.string() ?: "{}")
            token = json.optString("session_token", "")
            if (token.isNotEmpty()) {
                dbHelper.addConnectedServer(srv["server_name"] ?: "", url, key, token)
            }
        }
    } catch (_: Exception) {}
    return token
}

// ==========================================
// 1. DASHBOARD SECTION (WITH TELEMETRY CHART & ANIMATIONS)
// ==========================================
@Composable
fun DashboardSection(dbHelper: DatabaseHelper, client: OkHttpClient, servers: List<Map<String, String>>) {
    var attachedItemsCount by remember { mutableStateOf("0") }
    var publicItemsCount by remember { mutableStateOf("0") }
    var privateItemsCount by remember { mutableStateOf("0") }
    val scope = rememberCoroutineScope()
    val clientId = remember { dbHelper.getClientInfo().first }
    val theme = dbHelper.getSetting("theme", "Dark Mode")
    val isDark = theme == "Dark Mode"
    val animationsEnabled = dbHelper.getSetting("animations", "On") == "On"
    val fontScale = getFontScaleMultiplier(dbHelper.getSetting("font_scale", "Medium"))
    val accentColor = parseHexColor(dbHelper.getSetting("accent_color", "#00B050"), AccentGreen)

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            AnimatedVisibility(
                visible = true,
                enter = if (animationsEnabled) fadeIn(animationSpec = tween(500)) + slideInVertically(animationSpec = tween(500)) else fadeIn()
            ) {
                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    Text(
                        "HUB Operations Dashboard",
                        fontSize = (20 * fontScale).sp,
                        fontWeight = FontWeight.Bold,
                        color = if (isDark) TextPrimary else LightTextPrimary
                    )
                }
            }
        }

        item {
            AnimatedVisibility(
                visible = true,
                enter = if (animationsEnabled) fadeIn(animationSpec = tween(600)) else fadeIn()
            ) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    MetricCard("Linked Spaces", servers.size.toString(), Modifier.weight(1f), isDark, fontScale)
                    MetricCard("Attached Items", attachedItemsCount, Modifier.weight(1f), isDark, fontScale)
                }
            }
        }
        item {
            AnimatedVisibility(
                visible = true,
                enter = if (animationsEnabled) fadeIn(animationSpec = tween(700)) else fadeIn()
            ) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    MetricCard("Public Items", publicItemsCount, Modifier.weight(1f), isDark, fontScale)
                    MetricCard("Private Items", privateItemsCount, Modifier.weight(1f), isDark, fontScale)
                }
            }
        }
        item {
            AnimatedVisibility(
                visible = true,
                enter = if (animationsEnabled) fadeIn(animationSpec = tween(800)) else fadeIn()
            ) {
                RealtimeChartWidget("Real-Time Network Telemetry & Throughput Monitor", isDark, accentColor, animationsEnabled, fontScale)
            }
        }
    }
}

@Composable
fun RealtimeChartWidget(title: String, isDark: Boolean, accentColor: Color, animationsEnabled: Boolean, fontScale: Float) {
    var dataPoints by remember { mutableStateOf(listOf(20, 35, 40, 30, 55, 70, 65, 80, 50, 60, 75, 90, 85, 60, 45, 65, 80)) }

    LaunchedEffect(animationsEnabled) {
        while (true) {
            delay(1000)
            if (animationsEnabled) {
                val newVal = Random.nextInt(25, 95)
                dataPoints = (dataPoints.drop(1) + newVal)
            }
        }
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
        border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
        modifier = Modifier.fillMaxWidth().height(300.dp) // Changed from 200.dp to 300.dp
    ) {
        Column(modifier = Modifier.padding(16.dp).fillMaxSize()) {
            Text(title.uppercase(), fontSize = (11 * fontScale).sp, fontWeight = FontWeight.Bold, color = accentColor)
            Spacer(modifier = Modifier.height(8.dp))
            Box(modifier = Modifier.fillMaxWidth().weight(1f)) {
                Canvas(modifier = Modifier.fillMaxSize()) {
                    val w = size.width
                    val h = size.height

                    // Grid lines
                    for (i in 1..3) {
                        val y = h * i / 4
                        drawLine(
                            color = if (isDark) Color(0xFF1E3A29) else Color(0xFFE2E8F0),
                            start = Offset(0f, y),
                            end = Offset(w, y),
                            strokeWidth = 1f
                        )
                    }

                    if (dataPoints.isNotEmpty()) {
                        val step = w / (dataPoints.size - 1).coerceAtLeast(1)
                        val path = Path().apply {
                            moveTo(0f, h)
                            dataPoints.forEachIndexed { idx, valItem ->
                                val x = idx * step
                                val y = h - (valItem / 100f) * (h - 10f)
                                if (idx == 0) moveTo(x, y) else lineTo(x, y)
                            }
                        }

                        val fillPath = Path().apply {
                            addPath(path)
                            lineTo(w, h)
                            lineTo(0f, h)
                            close()
                        }

                        // Gradient fill under curve
                        drawPath(
                            path = fillPath,
                            brush = Brush.verticalGradient(
                                colors = listOf(accentColor.copy(alpha = 0.4f), accentColor.copy(alpha = 0.0f)),
                                startY = 0f,
                                endY = h
                            ),
                            style = Fill
                        )

                        // Line stroke
                        drawPath(
                            path = path,
                            color = accentColor,
                            style = Stroke(width = 3f)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun MetricCard(title: String, value: String, modifier: Modifier = Modifier, isDark: Boolean, fontScale: Float = 1.0f) {
    Card(
        colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
        border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
        modifier = modifier
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(value, fontSize = (22 * fontScale).sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            Spacer(modifier = Modifier.height(4.dp))
            Text(title.uppercase(), fontSize = (11 * fontScale).sp, fontWeight = FontWeight.Bold, color = if (isDark) TextSecondary else LightTextSecondary)
        }
    }
}

// ==========================================
// 2. MY DEVICE SECTION
// ==========================================
@Composable
fun MyDeviceSection(
    dbHelper: DatabaseHelper,
    client: OkHttpClient,
    clientIdProvider: DatabaseHelper,
    servers: List<Map<String, String>>,
    onServersChanged: (List<Map<String, String>>) -> Unit,
    remoteFiles: List<JSONObject>,
    onRemoteFilesChanged: (List<JSONObject>) -> Unit,
    onLogAdded: (String) -> Unit
) {
    val clientId = remember { clientIdProvider.getClientInfo().first }
    var isModerator by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val theme = dbHelper.getSetting("theme", "Dark Mode")
    val isDark = theme == "Dark Mode"
    val fontScale = getFontScaleMultiplier(dbHelper.getSetting("font_scale", "Medium"))

    LaunchedEffect(servers) {
        while (true) {
            launch(Dispatchers.IO) {
                var modStatus = false
                for (srv in servers) {
                    try {
                        val token = ensureValidSession(client, dbHelper, srv, clientId)
                        val req = Request.Builder()
                            .url("${srv["url"]}/api/user/profile")
                            .header("X-Client-ID", clientId)
                            .header("X-Session-Token", token)
                            .header("X-Server-Key", srv["server_key"] ?: "")
                            .header("bypass-tunnel-reminder", "true")
                            .header("User-Agent", "NairobiHubClient/1.0")
                            .get()
                            .build()
                        val res = client.newCall(req).execute()
                        if (res.isSuccessful) {
                            val json = JSONObject(res.body?.string() ?: "{}")
                            if (json.optString("role") == "moderator") {
                                modStatus = true
                                break
                            }
                        }
                    } catch (_: Exception) {}
                }
                withContext(Dispatchers.Main) {
                    isModerator = modStatus
                }
            }
            delay(5000)
        }
    }

    var subTab by remember { mutableStateOf(0) }
    val baseSubTabs = mutableListOf("Spaces", "Explore Spaces", "Search Channels")
    if (isModerator) {
        baseSubTabs.add("Moderator Panel")
    }

    var showAddServerDialog by remember { mutableStateOf(false) }
    var showProfileDialog by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Button(
                onClick = {
                    scope.launch(Dispatchers.IO) {
                        var addedCount = 0
                        for (srv in servers) {
                            try {
                                val token = ensureValidSession(client, dbHelper, srv, clientId)
                                val req = Request.Builder()
                                    .url("${srv["url"]}/api/links")
                                    .header("X-Client-ID", clientId)
                                    .header("X-Session-Token", token)
                                    .header("X-Server-Key", srv["server_key"] ?: "")
                                    .header("bypass-tunnel-reminder", "true")
                                    .header("User-Agent", "NairobiHubClient/1.0")
                                    .get()
                                    .build()
                                val res = client.newCall(req).execute()
                                if (res.isSuccessful) {
                                    val jsonArr = JSONArray(res.body?.string() ?: "[]")
                                    for (i in 0 until jsonArr.length()) {
                                        val itemObj = jsonArr.getJSONObject(i)
                                        itemObj.put("origin_server", srv["server_name"])
                                        dbHelper.addOfflineResource(itemObj)
                                        addedCount++
                                    }
                                }
                            } catch (_: Exception) {}
                        }
                        withContext(Dispatchers.Main) {
                            val msg = "Added $addedCount items from all spaces to offline mode"
                            showNotificationToast(context, dbHelper, msg, "All System Events")
                            onLogAdded("Successfully added $addedCount items from all spaces to offline mode.")
                        }
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                modifier = Modifier.weight(1f)
            ) {
                Text("Add All Items Offline", fontSize = (11 * fontScale).sp, color = Color.White)
            }

            Button(
                onClick = { showProfileDialog = true },
                colors = ButtonDefaults.buttonColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary),
                modifier = Modifier.weight(1f)
            ) {
                Text("My Profile", fontSize = (11 * fontScale).sp, color = if (isDark) TextPrimary else LightTextPrimary)
            }

            Button(
                onClick = { showAddServerDialog = true },
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                modifier = Modifier.weight(1f)
            ) {
                Text("+ Connect Space", fontSize = (11 * fontScale).sp, color = Color.White)
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        ScrollableTabRow(
            selectedTabIndex = subTab,
            containerColor = if (isDark) CardBackground else LightCardBackground,
            contentColor = MaterialTheme.colorScheme.primary,
            edgePadding = 0.dp
        ) {
            baseSubTabs.forEachIndexed { index, title ->
                Tab(
                    selected = subTab == index,
                    onClick = { subTab = index },
                    text = { Text(title, color = if (subTab == index) MaterialTheme.colorScheme.primary else if (isDark) TextSecondary else LightTextSecondary, fontWeight = FontWeight.Bold, fontSize = (12 * fontScale).sp) }
                )
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        val currentTabTitle = baseSubTabs.getOrNull(subTab) ?: "Spaces"
        when (currentTabTitle) {
            "Spaces" -> SpacesListTab(dbHelper, client, servers, onServersChanged, onLogAdded, fontScale)
            "Explore Spaces" -> ExploreFilesTab(dbHelper, client, clientId, servers, remoteFiles, onRemoteFilesChanged, isModerator, onLogAdded, fontScale)
            "Search Channels" -> SearchChannelsTab(dbHelper, client, servers, onServersChanged, onLogAdded, fontScale)
            "Moderator Panel" -> ModeratorPanelTab(dbHelper, client, clientId, servers, onLogAdded, fontScale)
        }
    }

    if (showAddServerDialog) {
        var spaceNameInput by remember { mutableStateOf("") }
        var spaceKeyInput by remember { mutableStateOf("") }
        AlertDialog(
            onDismissRequest = { showAddServerDialog = false },
            title = { Text("Connect New Space", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Enter space subdomain and access key.", color = if (isDark) TextSecondary else LightTextSecondary)
                    OutlinedTextField(
                        value = spaceNameInput,
                        onValueChange = { spaceNameInput = it },
                        label = { Text("Subdomain (e.g. nairobi-hub)") }
                    )
                    OutlinedTextField(
                        value = spaceKeyInput,
                        onValueChange = { spaceKeyInput = it },
                        label = { Text("16-character space key") }
                    )
                }
            },
            confirmButton = {
                Button(onClick = {
                    val name = spaceNameInput.trim().lowercase().replace("https://", "").replace(".loca.lt", "")
                    val key = spaceKeyInput.trim()
                    val url = "https://$name.loca.lt"
                    scope.launch(Dispatchers.IO) {
                        try {
                            val body = JSONObject().put("username", dbHelper.getClientInfo().second).toString()
                            val req = Request.Builder()
                                .url("$url/api/auth/connect")
                                .header("X-Client-ID", clientId)
                                .header("X-Server-Key", key)
                                .header("bypass-tunnel-reminder", "true")
                                .header("User-Agent", "NairobiHubClient/1.0")
                                .post(body.toRequestBody("application/json".toMediaType()))
                                .build()
                            val resp = client.newCall(req).execute()
                            val token = if (resp.isSuccessful) JSONObject(resp.body?.string() ?: "{}").optString("session_token", "") else ""
                            dbHelper.addConnectedServer(name, url, key, token)
                            withContext(Dispatchers.Main) {
                                onServersChanged(dbHelper.getConnectedServers())
                                showAddServerDialog = false
                                val logMsg = "Successfully connected to space: $name"
                                showNotificationToast(context, dbHelper, logMsg, "Connection State Changes Only")
                                onLogAdded(logMsg)
                            }
                        } catch (e: Exception) {
                            withContext(Dispatchers.Main) {
                                val errMsg = "Failed connecting to space: ${e.localizedMessage}"
                                showNotificationToast(context, dbHelper, errMsg, "Errors & Warnings Only")
                                onLogAdded(errMsg)
                            }
                        }
                    }
                }) {
                    Text("Connect & Save")
                }
            },
            dismissButton = {
                Button(onClick = { showAddServerDialog = false }) { Text("Cancel") }
            }
        )
    }

    if (showProfileDialog) {
        val (cId, currentUsername, currentDob) = remember { dbHelper.getClientInfo() }
        var usernameInput by remember { mutableStateOf(currentUsername) }
        var dobInput by remember { mutableStateOf(currentDob) }
        AlertDialog(
            onDismissRequest = { showProfileDialog = false },
            title = { Text("My Profile", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Client ID: $cId", fontSize = 12.sp, color = if (isDark) TextSecondary else LightTextSecondary)
                    OutlinedTextField(value = usernameInput, onValueChange = { usernameInput = it }, label = { Text("Username") })
                    OutlinedTextField(value = dobInput, onValueChange = { dobInput = it }, label = { Text("Date of Birth (YYYY-MM-DD)") })
                }
            },
            confirmButton = {
                Button(onClick = {
                    dbHelper.updateClientProfile(usernameInput, dobInput)
                    showProfileDialog = false
                    val msg = "Updated client profile successfully."
                    showNotificationToast(context, dbHelper, msg, "All System Events")
                    onLogAdded(msg)
                }) {
                    Text("Save Profile")
                }
            },
            dismissButton = {
                Button(onClick = { showProfileDialog = false }) { Text("Close") }
            }
        )
    }
}

@Composable
fun SpacesListTab(
    dbHelper: DatabaseHelper,
    client: OkHttpClient,
    servers: List<Map<String, String>>,
    onServersChanged: (List<Map<String, String>>) -> Unit,
    onLogAdded: (String) -> Unit,
    fontScale: Float
) {
    var selectedServerForMenu by remember { mutableStateOf<Map<String, String>?>(null) }
    var editServerDialog by remember { mutableStateOf<Map<String, String>?>(null) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val theme = dbHelper.getSetting("theme", "Dark Mode")
    val isDark = theme == "Dark Mode"

    LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxSize()) {
        items(servers) { srv ->
            Card(
                colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
                modifier = Modifier.fillMaxWidth().clickable {
                    selectedServerForMenu = srv
                }
            ) {
                Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(12.dp).background(StatusGreen, RoundedCornerShape(6.dp)))
                    Spacer(modifier = Modifier.width(12.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(srv["server_name"] ?: "", fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = if (isDark) TextPrimary else LightTextPrimary)
                        Text(srv["url"] ?: "", color = if (isDark) TextSecondary else LightTextSecondary, fontSize = (12 * fontScale).sp)
                    }
                    IconButton(onClick = { selectedServerForMenu = srv }) {
                        Icon(Icons.Default.MoreVert, contentDescription = "Menu", tint = if (isDark) TextPrimary else LightTextPrimary)
                    }
                }
            }
        }
    }

    if (selectedServerForMenu != null) {
        val srv = selectedServerForMenu!!
        AlertDialog(
            onDismissRequest = { selectedServerForMenu = null },
            title = { Text("Space Actions: ${srv["server_name"]}", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            selectedServerForMenu = null
                            editServerDialog = srv
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        Text("Edit Space Details")
                    }
                    Button(
                        onClick = {
                            dbHelper.removeConnectedServer(srv["server_name"] ?: "")
                            onServersChanged(dbHelper.getConnectedServers())
                            val msg = "Removed linked space: ${srv["server_name"]}"
                            showNotificationToast(context, dbHelper, msg, "Connection State Changes Only")
                            onLogAdded(msg)
                            selectedServerForMenu = null
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = StatusRed)
                    ) {
                        Text("Remove Space")
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                Button(onClick = { selectedServerForMenu = null }) { Text("Close") }
            }
        )
    }

    if (editServerDialog != null) {
        val srv = editServerDialog!!
        var editName by remember { mutableStateOf(srv["server_name"] ?: "") }
        var editKey by remember { mutableStateOf(srv["server_key"] ?: "") }

        AlertDialog(
            onDismissRequest = { editServerDialog = null },
            title = { Text("Edit Space: ${srv["server_name"]}", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = editName, onValueChange = { editName = it }, label = { Text("Space Name") })
                    OutlinedTextField(value = editKey, onValueChange = { editKey = it }, label = { Text("Space Key") })
                }
            },
            confirmButton = {
                Button(onClick = {
                    val newName = editName.trim().lowercase().replace("https://", "").replace(".loca.lt", "")
                    val newUrl = "https://$newName.loca.lt"
                    val newKey = editKey.trim()
                    scope.launch(Dispatchers.IO) {
                        dbHelper.removeConnectedServer(srv["server_name"] ?: "")
                        dbHelper.addConnectedServer(newName, newUrl, newKey, srv["session_token"] ?: "")
                        withContext(Dispatchers.Main) {
                            onServersChanged(dbHelper.getConnectedServers())
                            editServerDialog = null
                            val msg = "Updated space: $newName"
                            showNotificationToast(context, dbHelper, msg, "Connection State Changes Only")
                            onLogAdded(msg)
                        }
                    }
                }) {
                    Text("Save Changes")
                }
            },
            dismissButton = {
                Button(onClick = { editServerDialog = null }) { Text("Cancel") }
            }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun ExploreFilesTab(
    dbHelper: DatabaseHelper,
    client: OkHttpClient,
    clientId: String,
    servers: List<Map<String, String>>,
    remoteFiles: List<JSONObject>,
    onRemoteFilesChanged: (List<JSONObject>) -> Unit,
    isModerator: Boolean,
    onLogAdded: (String) -> Unit,
    fontScale: Float
) {
    var exploreSubTab by remember { mutableStateOf(0) }
    val exploreTabs = listOf("Explorer", "Bookmark", "Save for Offline Mode")
    var searchQuery by remember { mutableStateOf("") }
    var showUploadDialog by remember { mutableStateOf(false) }

    var bookmarks by remember { mutableStateOf(dbHelper.getFavoriteResources()) }
    var offlineItems by remember { mutableStateOf(dbHelper.getOfflineResources()) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val theme = dbHelper.getSetting("theme", "Dark Mode")
    val isDark = theme == "Dark Mode"

    var contextMenuFile by remember { mutableStateOf<JSONObject?>(null) }
    var editFileDialog by remember { mutableStateOf<JSONObject?>(null) }

    val providersList = listOf("Google Drive", "Dropbox", "OneDrive", "Mega", "Direct/Other")
    val itemTypesList = listOf("folder", "unknown file", "audio", "video", "word", "excel", "powerpoint", "image", "txt document")

    LaunchedEffect(servers) {
        scope.launch(Dispatchers.IO) {
            val fetchedList = mutableListOf<JSONObject>()
            for (srv in servers) {
                try {
                    val token = ensureValidSession(client, dbHelper, srv, clientId)
                    val req = Request.Builder()
                        .url("${srv["url"]}/api/links")
                        .header("X-Client-ID", clientId)
                        .header("X-Session-Token", token)
                        .header("X-Server-Key", srv["server_key"] ?: "")
                        .header("bypass-tunnel-reminder", "true")
                        .header("User-Agent", "NairobiHubClient/1.0")
                        .get()
                        .build()
                    val res = client.newCall(req).execute()
                    if (res.isSuccessful) {
                        val jsonArr = JSONArray(res.body?.string() ?: "[]")
                        for (i in 0 until jsonArr.length()) {
                            val itemObj = jsonArr.getJSONObject(i)
                            itemObj.put("origin_server", srv["server_name"])
                            itemObj.put("server_url", srv["url"])
                            fetchedList.add(itemObj)
                        }
                    }
                } catch (_: Exception) {}
            }
            withContext(Dispatchers.Main) {
                onRemoteFilesChanged(fetchedList)
            }
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        ScrollableTabRow(
            selectedTabIndex = exploreSubTab,
            containerColor = if (isDark) CardBackground else LightCardBackground,
            contentColor = MaterialTheme.colorScheme.primary,
            edgePadding = 0.dp
        ) {
            exploreTabs.forEachIndexed { index, title ->
                Tab(
                    selected = exploreSubTab == index,
                    onClick = { exploreSubTab = index },
                    text = { Text(title, color = if (exploreSubTab == index) MaterialTheme.colorScheme.primary else if (isDark) TextSecondary else LightTextSecondary, fontWeight = FontWeight.Bold, fontSize = (11 * fontScale).sp) }
                )
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        when (exploreSubTab) {
            0 -> {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = searchQuery,
                        onValueChange = { searchQuery = it },
                        placeholder = { Text("Search files & links...", color = if (isDark) TextSecondary else LightTextSecondary) },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(8.dp)
                    )
                    Button(
                        onClick = { showUploadDialog = true },
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "Attach Link", modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Attach Link", fontSize = (11 * fontScale).sp, color = Color.White)
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxSize()) {
                    val filtered = remoteFiles.filter {
                        it.optString("title", "").contains(searchQuery, true) ||
                                it.optString("username", "").contains(searchQuery, true)
                    }
                    items(filtered) { file ->
                        val linkId = file.optInt("id", 0)
                        val title = file.optString("title", "")
                        val url = file.optString("url", "")
                        val itemType = file.optString("item_type", "folder")
                        val provider = file.optString("provider", "Direct/Other")
                        val isPublic = file.optBoolean("is_public", true)
                        val originServer = file.optString("origin_server", "")

                        Card(
                            colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                            border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
                            modifier = Modifier
                                .fillMaxWidth()
                                .combinedClickable(
                                    onClick = {
                                        val urlIntent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                                        context.startActivity(urlIntent)
                                    },
                                    onLongClick = { contextMenuFile = file }
                                )
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp).fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(getItemIcon(itemType), contentDescription = null, tint = if (isPublic) StatusGreen else StatusRed, modifier = Modifier.size(32.dp))
                                Spacer(modifier = Modifier.width(12.dp))
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(title, fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = if (isDark) TextPrimary else LightTextPrimary)
                                    Text("By: ${file.optString("username")} | [$provider] | ${if (isPublic) "Public" else "Private"}", color = if (isDark) TextSecondary else LightTextSecondary, fontSize = (11 * fontScale).sp)
                                }
                                IconButton(onClick = {
                                    dbHelper.addFavoriteResource(originServer, linkId, title, url, itemType)
                                    bookmarks = dbHelper.getFavoriteResources()
                                    val msg = "Bookmarked: $title"
                                    showNotificationToast(context, dbHelper, msg, "All System Events")
                                }) {
                                    Icon(Icons.Default.Star, contentDescription = "Bookmark", tint = Color(0xFFFFD700))
                                }
                                IconButton(onClick = {
                                    dbHelper.addOfflineResource(file)
                                    offlineItems = dbHelper.getOfflineResources()
                                    val msg = "Saved for offline: $title"
                                    showNotificationToast(context, dbHelper, msg, "All System Events")
                                }) {
                                    Icon(Icons.Default.Download, contentDescription = "Offline", tint = MaterialTheme.colorScheme.primary)
                                }
                            }
                        }
                    }
                }
            }
            1 -> {
                Text("Bookmarked Resources", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary, fontSize = (14 * fontScale).sp)
                Spacer(modifier = Modifier.height(8.dp))
                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxSize()) {
                    items(bookmarks) { bm ->
                        val itemType = bm["item_type"]?.toString() ?: "folder"
                        Card(
                            colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                            border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp).fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(getItemIcon(itemType), contentDescription = null, tint = Color(0xFFFFD700), modifier = Modifier.size(28.dp))
                                Spacer(modifier = Modifier.width(12.dp))
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(bm["title"].toString(), fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = if (isDark) TextPrimary else LightTextPrimary)
                                    Text("Space: ${bm["server_name"]}", color = if (isDark) TextSecondary else LightTextSecondary, fontSize = (11 * fontScale).sp)
                                }
                                IconButton(onClick = {
                                    dbHelper.removeFavoriteResource(bm["server_name"].toString(), bm["link_id"].toString().toInt())
                                    bookmarks = dbHelper.getFavoriteResources()
                                    val msg = "Bookmark removed"
                                    showNotificationToast(context, dbHelper, msg, "All System Events")
                                }) {
                                    Icon(Icons.Default.Delete, contentDescription = "Remove Bookmark", tint = StatusRed)
                                }
                            }
                        }
                    }
                }
            }
            2 -> {
                Text("Offline Resources Library", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary, fontSize = (14 * fontScale).sp)
                Spacer(modifier = Modifier.height(8.dp))
                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxSize()) {
                    items(offlineItems) { off ->
                        val itemType = off["item_type"]?.toString() ?: "folder"
                        Card(
                            colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                            border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp).fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(getItemIcon(itemType), contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(28.dp))
                                Spacer(modifier = Modifier.width(12.dp))
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(off["title"].toString(), fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = if (isDark) TextPrimary else LightTextPrimary)
                                    Text("By: ${off["username"]}", color = if (isDark) TextSecondary else LightTextSecondary, fontSize = (11 * fontScale).sp)
                                }
                                IconButton(onClick = {
                                    dbHelper.removeOfflineResource(off["origin_server"].toString(), off["id"].toString().toInt())
                                    offlineItems = dbHelper.getOfflineResources()
                                    val msg = "Removed offline item"
                                    showNotificationToast(context, dbHelper, msg, "All System Events")
                                }) {
                                    Icon(Icons.Default.Delete, contentDescription = "Remove Offline", tint = StatusRed)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if (contextMenuFile != null) {
        val file = contextMenuFile!!
        val title = file.optString("title", "")
        val url = file.optString("url", "")
        val linkId = file.optInt("id", 0)
        val fileUserId = file.optString("user_id", "")
        val originServer = file.optString("origin_server", "")

        val canModify = (fileUserId == clientId)

        AlertDialog(
            onDismissRequest = { contextMenuFile = null },
            title = { Text("File Options: $title", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            contextMenuFile = null
                            val urlIntent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                            context.startActivity(urlIntent)
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        Text("Open Link in Browser")
                    }
                    if (canModify) {
                        Button(
                            onClick = {
                                contextMenuFile = null
                                editFileDialog = file
                            },
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                            border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary)
                        ) {
                            Text("Edit Attachment", color = if (isDark) TextPrimary else LightTextPrimary)
                        }
                        Button(
                            onClick = {
                                contextMenuFile = null
                                scope.launch(Dispatchers.IO) {
                                    try {
                                        val srv = servers.firstOrNull { it["server_name"] == originServer }
                                        if (srv != null) {
                                            val token = ensureValidSession(client, dbHelper, srv, clientId)
                                            val req = Request.Builder()
                                                .url("${srv["url"]}/api/links?id=$linkId")
                                                .header("X-Client-ID", clientId)
                                                .header("X-Session-Token", token)
                                                .header("X-Server-Key", srv["server_key"] ?: "")
                                                .header("bypass-tunnel-reminder", "true")
                                                .delete()
                                                .build()
                                            val res = client.newCall(req).execute()
                                            withContext(Dispatchers.Main) {
                                                if (res.isSuccessful) {
                                                    val msg = "Successfully deleted file: $title"
                                                    showNotificationToast(context, dbHelper, msg, "All System Events")
                                                    onLogAdded(msg)
                                                }
                                            }
                                        }
                                    } catch (_: Exception) {}
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(containerColor = StatusRed)
                        ) {
                            Text("Delete Attachment")
                        }
                    } else {
                        Text("You can only edit files that belong to you.", color = StatusRed, fontSize = 11.sp)
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                Button(onClick = { contextMenuFile = null }) { Text("Close") }
            }
        )
    }

    if (editFileDialog != null) {
        val file = editFileDialog!!
        val linkId = file.optInt("id", 0)
        val originServer = file.optString("origin_server", "")

        var editTitle by remember { mutableStateOf(file.optString("title", "")) }
        var editUrl by remember { mutableStateOf(file.optString("url", "")) }
        var editProvider by remember { mutableStateOf(file.optString("provider", providersList.first())) }
        var editItemType by remember { mutableStateOf(file.optString("item_type", "folder")) }
        var editIsPublic by remember { mutableStateOf(file.optBoolean("is_public", true)) }

        var providerExpanded by remember { mutableStateOf(false) }
        var typeExpanded by remember { mutableStateOf(false) }

        AlertDialog(
            onDismissRequest = { editFileDialog = null },
            title = { Text("Edit Attachment", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = editTitle, onValueChange = { editTitle = it }, label = { Text("Resource Title") })
                    OutlinedTextField(value = editUrl, onValueChange = { editUrl = it }, label = { Text("URL") })

                    Box(modifier = Modifier.fillMaxWidth()) {
                        OutlinedButton(onClick = { providerExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                            Text("Provider: $editProvider", color = if (isDark) TextPrimary else LightTextPrimary)
                        }
                        DropdownMenu(expanded = providerExpanded, onDismissRequest = { providerExpanded = false }) {
                            providersList.forEach { provider ->
                                DropdownMenuItem(
                                    text = { Text(provider, color = if (isDark) TextPrimary else LightTextPrimary) },
                                    onClick = {
                                        editProvider = provider
                                        providerExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    Box(modifier = Modifier.fillMaxWidth()) {
                        OutlinedButton(onClick = { typeExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                            Text("Item Type: $editItemType", color = if (isDark) TextPrimary else LightTextPrimary)
                        }
                        DropdownMenu(expanded = typeExpanded, onDismissRequest = { typeExpanded = false }) {
                            itemTypesList.forEach { t ->
                                DropdownMenuItem(
                                    text = { Text(t, color = if (isDark) TextPrimary else LightTextPrimary) },
                                    onClick = {
                                        editItemType = t
                                        typeExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = editIsPublic, onCheckedChange = { editIsPublic = it })
                        Text(if (editIsPublic) "Public Access" else "Private Access", color = if (isDark) TextPrimary else LightTextPrimary)
                    }
                }
            },
            confirmButton = {
                Button(onClick = {
                    scope.launch(Dispatchers.IO) {
                        try {
                            val targetSrv = servers.firstOrNull { it["server_name"] == originServer } ?: servers.firstOrNull()
                            if (targetSrv != null) {
                                val token = ensureValidSession(client, dbHelper, targetSrv, clientId)
                                val payload = JSONObject()
                                    .put("id", linkId)
                                    .put("title", editTitle.trim())
                                    .put("url", editUrl.trim())
                                    .put("provider", editProvider)
                                    .put("item_type", editItemType)
                                    .put("is_public", if (editIsPublic) 1 else 0)
                                    .toString()

                                val req = Request.Builder()
                                    .url("${targetSrv["url"]}/api/links")
                                    .header("X-Client-ID", clientId)
                                    .header("X-Session-Token", token)
                                    .header("X-Server-Key", targetSrv["server_key"] ?: "")
                                    .header("bypass-tunnel-reminder", "true")
                                    .put(payload.toRequestBody("application/json".toMediaType()))
                                    .build()

                                val resp = client.newCall(req).execute()
                                withContext(Dispatchers.Main) {
                                    if (resp.isSuccessful) {
                                        editFileDialog = null
                                        val msg = "Updated attachment: $editTitle"
                                        showNotificationToast(context, dbHelper, msg, "All System Events")
                                        onLogAdded(msg)
                                    } else {
                                        val errMsg = "Failed to update attachment"
                                        showNotificationToast(context, dbHelper, errMsg, "Errors & Warnings Only")
                                    }
                                }
                            }
                        } catch (e: Exception) {
                            withContext(Dispatchers.Main) {
                                val errMsg = "Error: ${e.localizedMessage}"
                                showNotificationToast(context, dbHelper, errMsg, "Errors & Warnings Only")
                            }
                        }
                    }
                }) {
                    Text("Save Changes")
                }
            },
            dismissButton = {
                Button(onClick = { editFileDialog = null }) { Text("Cancel") }
            }
        )
    }

    if (showUploadDialog) {
        var uploadTitle by remember { mutableStateOf("") }
        var uploadUrl by remember { mutableStateOf("") }
        var selectedProvider by remember { mutableStateOf(providersList.first()) }
        var selectedItemType by remember { mutableStateOf("folder") }
        var isPublic by remember { mutableStateOf(true) }

        var providerExpanded by remember { mutableStateOf(false) }
        var typeExpanded by remember { mutableStateOf(false) }

        AlertDialog(
            onDismissRequest = { showUploadDialog = false },
            title = { Text("Upload / Attach Resource", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = uploadTitle, onValueChange = { uploadTitle = it }, label = { Text("Resource Title") })
                    OutlinedTextField(value = uploadUrl, onValueChange = { uploadUrl = it }, label = { Text("URL (e.g. https://...)") })

                    Box(modifier = Modifier.fillMaxWidth()) {
                        OutlinedButton(onClick = { providerExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                            Text("Provider: $selectedProvider", color = if (isDark) TextPrimary else LightTextPrimary)
                        }
                        DropdownMenu(expanded = providerExpanded, onDismissRequest = { providerExpanded = false }) {
                            providersList.forEach { provider ->
                                DropdownMenuItem(
                                    text = { Text(provider, color = if (isDark) TextPrimary else LightTextPrimary) },
                                    onClick = {
                                        selectedProvider = provider
                                        providerExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    Box(modifier = Modifier.fillMaxWidth()) {
                        OutlinedButton(onClick = { typeExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                            Text("Item Type: $selectedItemType", color = if (isDark) TextPrimary else LightTextPrimary)
                        }
                        DropdownMenu(expanded = typeExpanded, onDismissRequest = { typeExpanded = false }) {
                            itemTypesList.forEach { t ->
                                DropdownMenuItem(
                                    text = { Text(t, color = if (isDark) TextPrimary else LightTextPrimary) },
                                    onClick = {
                                        selectedItemType = t
                                        typeExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = isPublic, onCheckedChange = { isPublic = it })
                        Text(if (isPublic) "Public Access" else "Private Access", color = if (isDark) TextPrimary else LightTextPrimary)
                    }
                }
            },
            confirmButton = {
                Button(onClick = {
                    val targetSrv = servers.firstOrNull()
                    if (targetSrv != null && uploadTitle.isNotBlank() && uploadUrl.isNotBlank()) {
                        scope.launch(Dispatchers.IO) {
                            try {
                                val token = ensureValidSession(client, dbHelper, targetSrv, clientId)
                                val payload = JSONObject()
                                    .put("title", uploadTitle.trim())
                                    .put("url", uploadUrl.trim())
                                    .put("provider", selectedProvider)
                                    .put("item_type", selectedItemType)
                                    .put("is_public", if (isPublic) 1 else 0)
                                    .toString()

                                val req = Request.Builder()
                                    .url("${targetSrv["url"]}/api/links")
                                    .header("X-Client-ID", clientId)
                                    .header("X-Session-Token", token)
                                    .header("X-Server-Key", targetSrv["server_key"] ?: "")
                                    .header("bypass-tunnel-reminder", "true")
                                    .post(payload.toRequestBody("application/json".toMediaType()))
                                    .build()

                                val resp = client.newCall(req).execute()
                                if (resp.isSuccessful) {
                                    withContext(Dispatchers.Main) {
                                        showUploadDialog = false
                                        val msg = "Successfully uploaded link: $uploadTitle"
                                        showNotificationToast(context, dbHelper, msg, "All System Events")
                                        onLogAdded(msg)
                                    }
                                }
                            } catch (_: Exception) {}
                        }
                    }
                }) {
                    Text("Attach & Publish")
                }
            },
            dismissButton = {
                Button(onClick = { showUploadDialog = false }) { Text("Cancel") }
            }
        )
    }
}

@Composable
fun SearchChannelsTab(
    dbHelper: DatabaseHelper,
    client: OkHttpClient,
    servers: List<Map<String, String>>,
    onServersChanged: (List<Map<String, String>>) -> Unit,
    onLogAdded: (String) -> Unit,
    fontScale: Float
) {
    var channelQuery by remember { mutableStateOf("") }
    var scanStatus by remember { mutableStateOf("Ready to scan channels...") }
    var discoveredServers by remember { mutableStateOf<List<Pair<String, String>>>(emptyList()) }
    var selectedChannelToConnect by remember { mutableStateOf<Pair<String, String>?>(null) }
    var spaceKeyInput by remember { mutableStateOf("") }
    var showKeyDialog by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val clientId = remember { dbHelper.getClientInfo().first }
    val context = LocalContext.current
    val theme = dbHelper.getSetting("theme", "Dark Mode")
    val isDark = theme == "Dark Mode"

    Column(verticalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxSize()) {
        Text("Discover active spaces broadcasting over .loca.lt signals.", color = if (isDark) TextSecondary else LightTextSecondary, fontSize = (13 * fontScale).sp)
        OutlinedTextField(
            value = channelQuery,
            onValueChange = { channelQuery = it },
            placeholder = { Text("Enter channel name...", color = if (isDark) TextSecondary else LightTextSecondary) },
            modifier = Modifier.fillMaxWidth()
        )
        Button(
            onClick = {
                scope.launch(Dispatchers.IO) {
                    scanStatus = "Scanning channels..."
                    val found = mutableListOf<Pair<String, String>>()
                    val commonNames = mutableListOf("nairobi-hub", "nairobi-drive-hub", "nairobi-county", "dev-hub", "shared-space", "hub", "test-server")
                    if (channelQuery.isNotEmpty() && !commonNames.contains(channelQuery.trim().lowercase())) {
                        commonNames.add(0, channelQuery.trim().lowercase())
                    }
                    for (name in commonNames) {
                        val url = "https://$name.loca.lt"
                        try {
                            val req = Request.Builder()
                                .url("$url/api/links")
                                .header("bypass-tunnel-reminder", "true")
                                .header("X-Client-ID", clientId)
                                .header("User-Agent", "NairobiHubSearch/1.0")
                                .get()
                                .build()
                            val resp = client.newCall(req).execute()
                            if (resp.isSuccessful) {
                                found.add(Pair(name, url))
                            }
                        } catch (_: Exception) {}
                    }
                    withContext(Dispatchers.Main) {
                        discoveredServers = found
                        scanStatus = "Scan finished. Found ${found.size} active space(s)."
                        val msg = "Scanned and found ${found.size} active channels."
                        showNotificationToast(context, dbHelper, msg, "Connection State Changes Only")
                        onLogAdded(msg)
                    }
                }
            },
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Scan / Search Channels", color = Color.White)
        }

        Text(scanStatus, color = if (isDark) TextSecondary else LightTextSecondary, fontSize = (12 * fontScale).sp)

        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxSize()) {
            items(discoveredServers) { srv ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                    border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
                    onClick = {
                        val currentServers = dbHelper.getConnectedServers()
                        val alreadyExists = currentServers.any { it["server_name"] == srv.first }
                        if (alreadyExists) {
                            val errMsg = "Space '${srv.first}' already exists"
                            showNotificationToast(context, dbHelper, errMsg, "Errors & Warnings Only")
                            return@Card
                        }
                        selectedChannelToConnect = srv
                        showKeyDialog = true
                    }
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("Active Space: ${srv.first} (Click to Connect)", fontWeight = FontWeight.Bold, fontSize = (15 * fontScale).sp, color = MaterialTheme.colorScheme.primary)
                        Text(srv.second, color = if (isDark) TextPrimary else LightTextPrimary, fontSize = (12 * fontScale).sp)
                    }
                }
            }
        }
    }

    if (showKeyDialog && selectedChannelToConnect != null) {
        AlertDialog(
            onDismissRequest = { showKeyDialog = false },
            title = { Text("Enter Space Access Key", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column {
                    Text("New clients require the random space key to register.", color = if (isDark) TextSecondary else LightTextSecondary)
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = spaceKeyInput,
                        onValueChange = { spaceKeyInput = it },
                        placeholder = { Text("16-character key") }
                    )
                }
            },
            confirmButton = {
                Button(onClick = {
                    val target = selectedChannelToConnect!!
                    scope.launch(Dispatchers.IO) {
                        try {
                            val body = JSONObject().put("username", dbHelper.getClientInfo().second).toString()
                            val req = Request.Builder()
                                .url("${target.second}/api/auth/connect")
                                .header("X-Client-ID", clientId)
                                .header("X-Server-Key", spaceKeyInput)
                                .header("bypass-tunnel-reminder", "true")
                                .header("User-Agent", "NairobiHubClient/1.0")
                                .post(body.toRequestBody("application/json".toMediaType()))
                                .build()
                            val resp = client.newCall(req).execute()
                            if (resp.isSuccessful) {
                                val json = JSONObject(resp.body?.string() ?: "{}")
                                val token = json.optString("session_token", "")
                                dbHelper.addConnectedServer(target.first, target.second, spaceKeyInput, token)
                                withContext(Dispatchers.Main) {
                                    onServersChanged(dbHelper.getConnectedServers())
                                    showKeyDialog = false
                                    val msg = "Successfully registered & connected to space: ${target.first}"
                                    showNotificationToast(context, dbHelper, msg, "Connection State Changes Only")
                                    onLogAdded(msg)
                                }
                            }
                        } catch (_: Exception) {}
                    }
                }) {
                    Text("Connect")
                }
            },
            dismissButton = {
                Button(onClick = { showKeyDialog = false }) { Text("Cancel") }
            }
        )
    }
}

// ==========================================
// 3. MODERATOR PANEL TAB
// ==========================================
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun ModeratorPanelTab(
    dbHelper: DatabaseHelper,
    client: OkHttpClient,
    clientId: String,
    servers: List<Map<String, String>>,
    onLogAdded: (String) -> Unit,
    fontScale: Float
) {
    var modFiles by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var contextMenuFile by remember { mutableStateOf<JSONObject?>(null) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val theme = dbHelper.getSetting("theme", "Dark Mode")
    val isDark = theme == "Dark Mode"

    LaunchedEffect(servers) {
        scope.launch(Dispatchers.IO) {
            val list = mutableListOf<JSONObject>()
            for (srv in servers) {
                try {
                    val token = ensureValidSession(client, dbHelper, srv, clientId)
                    val req = Request.Builder()
                        .url("${srv["url"]}/api/links")
                        .header("X-Client-ID", clientId)
                        .header("X-Session-Token", token)
                        .header("X-Server-Key", srv["server_key"] ?: "")
                        .header("bypass-tunnel-reminder", "true")
                        .header("User-Agent", "NairobiHubClient/1.0")
                        .get()
                        .build()
                    val res = client.newCall(req).execute()
                    if (res.isSuccessful) {
                        val arr = JSONArray(res.body?.string() ?: "[]")
                        for (i in 0 until arr.length()) {
                            val obj = arr.getJSONObject(i)
                            obj.put("origin_url", srv["url"])
                            obj.put("origin_server", srv["server_name"])
                            list.add(obj)
                        }
                    }
                } catch (_: Exception) {}
            }
            withContext(Dispatchers.Main) {
                modFiles = list
            }
        }
    }

    Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxSize()) {
        Text("Moderator Oversight Panel (Long press for extra actions)", fontWeight = FontWeight.Bold, fontSize = (14 * fontScale).sp, color = MaterialTheme.colorScheme.primary)
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxSize()) {
            items(modFiles) { file ->
                val isHidden = file.optBoolean("is_hidden", false)
                Card(
                    colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                    border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
                    modifier = Modifier
                        .fillMaxWidth()
                        .combinedClickable(
                            onClick = {},
                            onLongClick = { contextMenuFile = file }
                        )
                ) {
                    Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(file.optString("title"), fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = if (isDark) TextPrimary else LightTextPrimary)
                            Text("By: ${file.optString("username")} | Space: ${file.optString("origin_server")} | ${if (isHidden) "Hidden" else "Visible"}", color = if (isDark) TextSecondary else LightTextSecondary, fontSize = (11 * fontScale).sp)
                        }
                    }
                }
            }
        }
    }

    if (contextMenuFile != null) {
        val file = contextMenuFile!!
        val title = file.optString("title", "")
        val url = file.optString("url", "")
        val linkId = file.optInt("id", 0)
        val originUrl = file.optString("origin_url", "")
        val isHidden = file.optBoolean("is_hidden", false)

        AlertDialog(
            onDismissRequest = { contextMenuFile = null },
            title = { Text("Moderator File Action: $title", color = if (isDark) TextPrimary else LightTextPrimary) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = {
                            contextMenuFile = null
                            val urlIntent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                            context.startActivity(urlIntent)
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        Text("Read File")
                    }
                    Button(
                        onClick = {
                            contextMenuFile = null
                            scope.launch(Dispatchers.IO) {
                                try {
                                    val payload = JSONObject()
                                        .put("link_id", linkId)
                                        .put("action", "hide")
                                        .put("is_hidden", if (isHidden) 0 else 1)
                                        .toString()
                                    val req = Request.Builder()
                                        .url("$originUrl/api/moderator/file_action")
                                        .header("X-Client-ID", clientId)
                                        .header("bypass-tunnel-reminder", "true")
                                        .post(payload.toRequestBody("application/json".toMediaType()))
                                        .build()
                                    client.newCall(req).execute()
                                    withContext(Dispatchers.Main) {
                                        val msg = "Moderator toggled visibility for file: $title"
                                        showNotificationToast(context, dbHelper, msg, "All System Events")
                                        onLogAdded(msg)
                                    }
                                } catch (_: Exception) {}
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary)
                    ) {
                        Text(if (isHidden) "Unhide from Users" else "Hide from Users", color = if (isDark) TextPrimary else LightTextPrimary)
                    }
                    Button(
                        onClick = {
                            contextMenuFile = null
                            scope.launch(Dispatchers.IO) {
                                try {
                                    val payload = JSONObject()
                                        .put("link_id", linkId)
                                        .put("action", "remove")
                                        .toString()
                                    val req = Request.Builder()
                                        .url("$originUrl/api/moderator/file_action")
                                        .header("X-Client-ID", clientId)
                                        .header("bypass-tunnel-reminder", "true")
                                        .post(payload.toRequestBody("application/json".toMediaType()))
                                        .build()
                                    client.newCall(req).execute()
                                    withContext(Dispatchers.Main) {
                                        val msg = "Moderator removed file: $title"
                                        showNotificationToast(context, dbHelper, msg, "Errors & Warnings Only")
                                        onLogAdded(msg)
                                    }
                                } catch (_: Exception) {}
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = StatusRed)
                    ) {
                        Text("Remove the File")
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                Button(onClick = { contextMenuFile = null }) { Text("Close") }
            }
        )
    }
}

// ==========================================
// 4. SETTINGS SECTION (CONTROL-ENABLED & PERSISTENT)
// ==========================================
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsSection(dbHelper: DatabaseHelper, logs: List<String>, onLogAdded: (String) -> Unit, onSettingsUpdated: () -> Unit) {
    var settingsSubTab by remember { mutableStateOf(0) }
    val settingTabs = listOf("Appearance & Display", "Behavior & Navigation", "Data, Storage & Sync", "Notifications & Alerts", "Activity Log")

    var themeSelection by remember { mutableStateOf(dbHelper.getSetting("theme", "Dark Mode")) }
    var accentColorInput by remember { mutableStateOf(dbHelper.getSetting("accent_color", "#00B050")) }
    var fontScaleSelection by remember { mutableStateOf(dbHelper.getSetting("font_scale", "Medium")) }
    var animEnabled by remember { mutableStateOf(dbHelper.getSetting("animations", "On")) }
    var highContrast by remember { mutableStateOf(dbHelper.getSetting("high_contrast", "Off")) }

    var defaultView by remember { mutableStateOf(dbHelper.getSetting("default_view", "Dashboard")) }

    var storageDir by remember { mutableStateOf(dbHelper.getSetting("storage_dir", "/storage/emulated/0/NairobiHub")) }
    var autosaveFreq by remember { mutableStateOf(dbHelper.getSetting("autosave_freq", "Every 15 minutes")) }

    var soundAlerts by remember { mutableStateOf(dbHelper.getSetting("notif_sound", "On")) }
    var bannerAlerts by remember { mutableStateOf(dbHelper.getSetting("notif_banner", "On")) }
    var eventFilter by remember { mutableStateOf(dbHelper.getSetting("notif_filter", "All System Events")) }

    var themeExpanded by remember { mutableStateOf(false) }
    var fontScaleExpanded by remember { mutableStateOf(false) }
    var animExpanded by remember { mutableStateOf(false) }
    var highContrastExpanded by remember { mutableStateOf(false) }
    var soundAlertsExpanded by remember { mutableStateOf(false) }
    var bannerAlertsExpanded by remember { mutableStateOf(false) }
    var defaultViewExpanded by remember { mutableStateOf(false) }
    var autosaveExpanded by remember { mutableStateOf(false) }
    var eventFilterExpanded by remember { mutableStateOf(false) }
    var showColorWheelDialog by remember { mutableStateOf(false) }

    val context = LocalContext.current
    val isDark = themeSelection == "Dark Mode"
    val fontScale = getFontScaleMultiplier(fontScaleSelection)
    val rainbowColors = listOf("#00B050", "#22C55E", "#3B82F6", "#8B5CF6", "#EC4899", "#EF4444", "#F59E0B", "#10B981")

    val textColor = if (isDark) TextPrimary else LightTextPrimary
    val subTextColor = if (isDark) TextSecondary else LightTextSecondary

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text("Settings App & System Preferences", fontSize = (18 * fontScale).sp, fontWeight = FontWeight.Bold, color = textColor, modifier = Modifier.weight(1f))
            Button(
                onClick = {
                    dbHelper.resetAllSettings()
                    themeSelection = "Dark Mode"
                    accentColorInput = "#00B050"
                    fontScaleSelection = "Medium"
                    animEnabled = "On"
                    defaultView = "Dashboard"
                    autosaveFreq = "Every 15 minutes"
                    soundAlerts = "On"
                    bannerAlerts = "On"
                    eventFilter = "All System Events"
                    highContrast = "Off"
                    val resetMsg = "Reset all system preferences to defaults."
                    showNotificationToast(context, dbHelper, resetMsg, "All System Events")
                    onLogAdded(resetMsg)
                    onSettingsUpdated()
                },
                colors = ButtonDefaults.buttonColors(containerColor = StatusRed)
            ) {
                Text("Reset All", fontSize = (11 * fontScale).sp, color = Color.White)
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        ScrollableTabRow(
            selectedTabIndex = settingsSubTab,
            containerColor = if (isDark) CardBackground else LightCardBackground,
            contentColor = MaterialTheme.colorScheme.primary,
            edgePadding = 0.dp
        ) {
            settingTabs.forEachIndexed { index, title ->
                Tab(
                    selected = settingsSubTab == index,
                    onClick = { settingsSubTab = index },
                    text = { Text(title, color = if (settingsSubTab == index) MaterialTheme.colorScheme.primary else subTextColor, fontWeight = FontWeight.Bold, fontSize = (11 * fontScale).sp) }
                )
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        when (settingsSubTab) {
            0 -> {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxSize()) {
                    item {
                        Card(colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground), border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor)) {
                            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                Text("Appearance & Display", fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = MaterialTheme.colorScheme.primary)

                                Text("Color Theme", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { themeExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(themeSelection, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = themeExpanded, onDismissRequest = { themeExpanded = false }) {
                                        listOf("Dark Mode", "Light Mode").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    themeSelection = item
                                                    themeExpanded = false
                                                    dbHelper.saveSetting("theme", item)
                                                    onSettingsUpdated()
                                                }
                                            )
                                        }
                                    }
                                }

                                Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    OutlinedTextField(
                                        value = accentColorInput,
                                        onValueChange = {
                                            accentColorInput = it
                                            dbHelper.saveSetting("accent_color", it)
                                            onSettingsUpdated()
                                        },
                                        label = { Text("Accent Color (Hex)") },
                                        modifier = Modifier.weight(1f)
                                    )
                                    Button(
                                        onClick = { showColorWheelDialog = true },
                                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                                    ) {
                                        Text("Rainbow Wheel", fontSize = (11 * fontScale).sp)
                                    }
                                }

                                Text("Font Size & Scaling", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { fontScaleExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(fontScaleSelection, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = fontScaleExpanded, onDismissRequest = { fontScaleExpanded = false }) {
                                        listOf("Small", "Medium", "Large", "Custom").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    fontScaleSelection = item
                                                    fontScaleExpanded = false
                                                    dbHelper.saveSetting("font_scale", item)
                                                }
                                            )
                                        }
                                    }
                                }

                                Text("Enable UI animations & fading", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { animExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(animEnabled, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = animExpanded, onDismissRequest = { animExpanded = false }) {
                                        listOf("On", "Off").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    animEnabled = item
                                                    animExpanded = false
                                                    dbHelper.saveSetting("animations", item)
                                                }
                                            )
                                        }
                                    }
                                }

                                Text("High Contrast Screen Reader Mode", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { highContrastExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(highContrast, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = highContrastExpanded, onDismissRequest = { highContrastExpanded = false }) {
                                        listOf("On", "Off").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    highContrast = item
                                                    highContrastExpanded = false
                                                    dbHelper.saveSetting("high_contrast", item)
                                                    onSettingsUpdated()
                                                }
                                            )
                                        }
                                    }
                                }

                                Button(
                                    onClick = {
                                        dbHelper.saveSetting("theme", themeSelection)
                                        dbHelper.saveSetting("accent_color", accentColorInput)
                                        dbHelper.saveSetting("font_scale", fontScaleSelection)
                                        dbHelper.saveSetting("animations", animEnabled)
                                        dbHelper.saveSetting("high_contrast", highContrast)
                                        val msg = "Updated appearance & accessibility preferences."
                                        showNotificationToast(context, dbHelper, msg, "All System Events")
                                        onLogAdded(msg)
                                        onSettingsUpdated()
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("Save Appearance Settings", color = Color.White)
                                }
                            }
                        }
                    }
                }
            }
            1 -> {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxSize()) {
                    item {
                        Card(colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground), border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor)) {
                            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                Text("Behavior & Navigation Preferences", fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = MaterialTheme.colorScheme.primary)

                                Text("Default Landing Page View", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { defaultViewExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(defaultView, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = defaultViewExpanded, onDismissRequest = { defaultViewExpanded = false }) {
                                        listOf("Dashboard", "My Device", "Settings").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    defaultView = item
                                                    defaultViewExpanded = false
                                                    dbHelper.saveSetting("default_view", item)
                                                }
                                            )
                                        }
                                    }
                                }

                                Button(
                                    onClick = {
                                        dbHelper.saveSetting("default_view", defaultView)
                                        val msg = "Updated behavior preferences."
                                        showNotificationToast(context, dbHelper, msg, "All System Events")
                                        onLogAdded(msg)
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("Save Behavior Settings", color = Color.White)
                                }
                            }
                        }
                    }
                }
            }
            2 -> {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxSize()) {
                    item {
                        Card(colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground), border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor)) {
                            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                Text("Data, Storage & Sync Management", fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = MaterialTheme.colorScheme.primary)

                                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Button(
                                        onClick = {
                                            dbHelper.clearCache()
                                            val msg = "Cleared local offline cache."
                                            showNotificationToast(context, dbHelper, msg, "All System Events")
                                            onLogAdded(msg)
                                        },
                                        colors = ButtonDefaults.buttonColors(containerColor = StatusRed),
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Text("Clear Cache")
                                    }
                                    Button(
                                        onClick = {
                                            val msg = "Exported user data and configurations."
                                            showNotificationToast(context, dbHelper, msg, "All System Events")
                                            onLogAdded(msg)
                                        },
                                        colors = ButtonDefaults.buttonColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary),
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Text("Export Data", color = textColor)
                                    }
                                }

                                OutlinedTextField(
                                    value = storageDir,
                                    onValueChange = {
                                        storageDir = it
                                        dbHelper.saveSetting("storage_dir", it)
                                    },
                                    label = { Text("Storage Directory Path") },
                                    modifier = Modifier.fillMaxWidth()
                                )

                                Text("Auto-Save Frequency", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { autosaveExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(autosaveFreq, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = autosaveExpanded, onDismissRequest = { autosaveExpanded = false }) {
                                        listOf("Every 5 minutes", "Every 15 minutes", "Every 30 minutes", "Manual only").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    autosaveFreq = item
                                                    autosaveExpanded = false
                                                    dbHelper.saveSetting("autosave_freq", item)
                                                }
                                            )
                                        }
                                    }
                                }

                                Button(
                                    onClick = {
                                        dbHelper.saveSetting("storage_dir", storageDir)
                                        dbHelper.saveSetting("autosave_freq", autosaveFreq)
                                        val msg = "Updated storage & sync configurations."
                                        showNotificationToast(context, dbHelper, msg, "All System Events")
                                        onLogAdded(msg)
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("Save Storage Settings", color = Color.White)
                                }
                            }
                        }
                    }
                }
            }
            3 -> {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxSize()) {
                    item {
                        Card(colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground), border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor)) {
                            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                Text("Notifications & Alerts", fontWeight = FontWeight.Bold, fontSize = (16 * fontScale).sp, color = MaterialTheme.colorScheme.primary)

                                Text("Sound Alerts", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { soundAlertsExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(soundAlerts, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = soundAlertsExpanded, onDismissRequest = { soundAlertsExpanded = false }) {
                                        listOf("On", "Off").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    soundAlerts = item
                                                    soundAlertsExpanded = false
                                                    dbHelper.saveSetting("notif_sound", item)
                                                }
                                            )
                                        }
                                    }
                                }

                                Text("In-App Banner Alerts (Toasts)", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { bannerAlertsExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(bannerAlerts, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = bannerAlertsExpanded, onDismissRequest = { bannerAlertsExpanded = false }) {
                                        listOf("On", "Off").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    bannerAlerts = item
                                                    bannerAlertsExpanded = false
                                                    dbHelper.saveSetting("notif_banner", item)
                                                }
                                            )
                                        }
                                    }
                                }

                                Text("Event Filters", color = subTextColor, fontSize = (12 * fontScale).sp)
                                Box(modifier = Modifier.fillMaxWidth()) {
                                    OutlinedButton(onClick = { eventFilterExpanded = true }, modifier = Modifier.fillMaxWidth()) {
                                        Text(eventFilter, color = textColor, fontSize = (14 * fontScale).sp)
                                    }
                                    DropdownMenu(expanded = eventFilterExpanded, onDismissRequest = { eventFilterExpanded = false }) {
                                        listOf("All System Events", "Errors & Warnings Only", "Connection State Changes Only").forEach { item ->
                                            DropdownMenuItem(
                                                text = { Text(item, color = textColor) },
                                                onClick = {
                                                    eventFilter = item
                                                    eventFilterExpanded = false
                                                    dbHelper.saveSetting("notif_filter", item)
                                                }
                                            )
                                        }
                                    }
                                }

                                Button(
                                    onClick = {
                                        dbHelper.saveSetting("notif_sound", soundAlerts)
                                        dbHelper.saveSetting("notif_banner", bannerAlerts)
                                        dbHelper.saveSetting("notif_filter", eventFilter)
                                        val msg = "Updated notification preferences."
                                        showNotificationToast(context, dbHelper, msg, "All System Events")
                                        onLogAdded(msg)
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("Save Notification Settings", color = Color.White)
                                }
                            }
                        }
                    }
                }
            }
            4 -> {
                Column(modifier = Modifier.fillMaxSize()) {
                    Text("System Activity Log", fontSize = (16 * fontScale).sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                    Spacer(modifier = Modifier.height(8.dp))
                    Card(
                        colors = CardDefaults.cardColors(containerColor = if (isDark) CardBackground else LightCardBackground),
                        border = BorderStroke(1.dp, if (isDark) BorderColor else LightBorderColor),
                        modifier = Modifier.fillMaxSize()
                    ) {
                        LazyColumn(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            items(logs) { log ->
                                Text(log, color = subTextColor, fontSize = (12 * fontScale).sp, fontFamily = FontFamily.Monospace)
                            }
                        }
                    }
                }
            }
        }
    }

    if (showColorWheelDialog) {
        AlertDialog(
            onDismissRequest = { showColorWheelDialog = false },
            title = { Text("Select Accent Color (Rainbow Wheel)", color = textColor) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Choose from the color spectrum below:", color = subTextColor, fontSize = 12.sp)

                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(24.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(
                                brush = Brush.horizontalGradient(
                                    colors = rainbowColors.map { parseHexColor(it, Color.Green) }
                                )
                            )
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        rainbowColors.forEach { hex ->
                            val color = parseHexColor(hex, Color.Green)
                            Box(
                                modifier = Modifier
                                    .size(32.dp)
                                    .clip(CircleShape)
                                    .background(color)
                                    .clickable {
                                        accentColorInput = hex
                                        showColorWheelDialog = false
                                        dbHelper.saveSetting("accent_color", hex)
                                        onSettingsUpdated()
                                        val msg = "Accent color updated to $hex"
                                        showNotificationToast(context, dbHelper, msg, "All System Events")
                                    }
                            )
                        }
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                Button(onClick = { showColorWheelDialog = false }) { Text("Close") }
            }
        )
    }
}

