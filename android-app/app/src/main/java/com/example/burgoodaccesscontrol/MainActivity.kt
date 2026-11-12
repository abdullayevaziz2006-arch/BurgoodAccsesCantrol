package com.example.burgoodaccesscontrol

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.*
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : ComponentActivity() {
    private var webView: WebView? = null
    // Standart faol server manzillari
    private val defaultServerUrl = "https://44.221.176.109.sslip.io"
    private val defaultLocalUrl = "http://10.70.7.144:8000"

    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null

    private val fileChooserLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (fileChooserCallback != null) {
            val results = WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data)
            fileChooserCallback?.onReceiveValue(results)
            fileChooserCallback = null
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val prefs = getSharedPreferences("burgood_prefs", Context.MODE_PRIVATE)

        setContent {
            val scope = rememberCoroutineScope()

            var serverUrl by remember {
                val saved = prefs.getString("server_url", null)
                mutableStateOf(
                    if (saved.isNullOrEmpty() || saved.startsWith("http://44.221.176.109") || (saved.contains("trycloudflare.com") && saved != defaultServerUrl)) {
                        defaultServerUrl
                    } else {
                        saved
                    }
                )
            }
            var authToken by remember { mutableStateOf(prefs.getString("auth_token", null)) }
            var authUserJson by remember { mutableStateOf(prefs.getString("auth_user", null)) }
            var authOrgJson by remember { mutableStateOf(prefs.getString("auth_org", null)) }

            // Login forma holatlari
            var usernameInput by remember { mutableStateOf("") }
            var passwordInput by remember { mutableStateOf("") }
            var isPasswordVisible by remember { mutableStateOf(false) }
            var isLoggingIn by remember { mutableStateOf(false) }
            var loginError by remember { mutableStateOf<String?>(null) }
            var showServerDialog by remember { mutableStateOf(false) }
            var tempServerUrl by remember { mutableStateOf(serverUrl) }


            // Web yuklanish
            var isWebLoading by remember { mutableStateOf(false) }

            val darkBg = Color(0xFF0A1122)
            val primaryBlue = Color(0xFF0084FF)
            val cyanAccent = Color(0xFF06B6D4)

            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(darkBg)
                    .statusBarsPadding()
                    .navigationBarsPadding()
            ) {
                // ========================================================
                // 1. AGAR TIZIMGA KIRILGAN BO'LSA - ASOSIY TIZIMNI KO'RSATISH
                // ========================================================
                if (!authToken.isNullOrEmpty()) {
                    AndroidView(
                        factory = { ctx ->
                            WebView(ctx).apply {
                                layoutParams = ViewGroup.LayoutParams(
                                    ViewGroup.LayoutParams.MATCH_PARENT,
                                    ViewGroup.LayoutParams.MATCH_PARENT
                                )
                                setBackgroundColor(android.graphics.Color.parseColor("#0A1122"))

                                settings.javaScriptEnabled = true
                                settings.domStorageEnabled = true
                                settings.databaseEnabled = true
                                settings.useWideViewPort = true
                                settings.loadWithOverviewMode = true
                                settings.allowFileAccess = true
                                settings.allowContentAccess = true
                                settings.cacheMode = WebSettings.LOAD_DEFAULT

                                webViewClient = object : WebViewClient() {
                                    override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                                        isWebLoading = true
                                        // Login ma'lumotlarini webview localStorage ga yuklash
                                        val tokenSafe = authToken ?: ""
                                        val userSafe = (authUserJson ?: "{}").replace("'", "\\'")
                                        val orgSafe = (authOrgJson ?: "{}").replace("'", "\\'")
                                        val injectJs = """
                                            try {
                                                localStorage.setItem('burgood_token', '$tokenSafe');
                                                localStorage.setItem('burgood_user', '$userSafe');
                                                localStorage.setItem('burgood_org', '$orgSafe');
                                            } catch(e) {}
                                        """.trimIndent()
                                        view?.evaluateJavascript(injectJs, null)
                                    }

                                    override fun onPageFinished(view: WebView?, url: String?) {
                                        isWebLoading = false
                                        view?.setBackgroundColor(android.graphics.Color.parseColor("#0A1122"))
                                    }
                                }

                                webChromeClient = object : WebChromeClient() {
                                    override fun onPermissionRequest(request: PermissionRequest?) {
                                        request?.grant(request.resources)
                                    }

                                    override fun onShowFileChooser(
                                        view: WebView?,
                                        filePathCallback: ValueCallback<Array<Uri>>?,
                                        fileChooserParams: FileChooserParams?
                                    ): Boolean {
                                        fileChooserCallback?.onReceiveValue(null)
                                        fileChooserCallback = filePathCallback

                                        try {
                                            val intent = fileChooserParams?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT).apply {
                                                addCategory(Intent.CATEGORY_OPENABLE)
                                                type = "image/*"
                                            }
                                            fileChooserLauncher.launch(intent)
                                            return true
                                        } catch (e: Exception) {
                                            fileChooserCallback?.onReceiveValue(null)
                                            fileChooserCallback = null
                                            return false
                                        }
                                    }
                                }

                                addJavascriptInterface(object {
                                    @JavascriptInterface
                                    fun logout() {
                                        runOnUiThread {
                                            prefs.edit()
                                                .remove("auth_token")
                                                .remove("auth_user")
                                                .remove("auth_org")
                                                .apply()
                                            authToken = null
                                            authUserJson = null
                                            authOrgJson = null
                                        }
                                    }
                                }, "AndroidBridge")

                                loadUrl(serverUrl)
                                webView = this
                            }
                        },
                        modifier = Modifier.fillMaxSize()
                    )

                    // Web yuklanish animatsiyasi
                    if (isWebLoading) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(darkBg.copy(alpha = 0.85f)),
                            contentAlignment = Alignment.Center
                        ) {
                            CircularProgressIndicator(color = cyanAccent, modifier = Modifier.size(44.dp))
                        }
                    }
                }

                // ========================================================
                // 2. AGAR KIRILMAGAN BO'LSA - FAQATGINA LOGIN VA PAROL OYNASI
                // ========================================================
                if (authToken.isNullOrEmpty()) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(darkBg)
                            .padding(horizontal = 28.dp, vertical = 32.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        // Burgood Logotipi
                        Box(
                            modifier = Modifier
                                .size(96.dp)
                                .clip(RoundedCornerShape(26.dp))
                                .background(Color(0xFF0F1E3D)),
                            contentAlignment = Alignment.Center
                        ) {
                            Image(
                                painter = painterResource(id = R.drawable.burgood_foreground),
                                contentDescription = "Burgood Logo",
                                modifier = Modifier.size(76.dp)
                            )
                        }

                        Spacer(modifier = Modifier.height(18.dp))

                        Text(
                            text = "BURGOOD ACCESS",
                            fontSize = 24.sp,
                            fontWeight = FontWeight.Black,
                            color = Color.White,
                            letterSpacing = 1.sp
                        )

                        Text(
                            text = "Xavfsizlik & Davomat Tizimi",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = cyanAccent,
                            letterSpacing = 1.2.sp
                        )

                        Spacer(modifier = Modifier.height(32.dp))

                        // Xatolik xabari chiqsa
                        if (!loginError.isNullOrEmpty()) {
                            Card(
                                colors = CardDefaults.cardColors(containerColor = Color(0xFF2D1515)),
                                shape = RoundedCornerShape(12.dp),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    text = loginError ?: "",
                                    color = Color(0xFFFCA5A5),
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Medium,
                                    modifier = Modifier.padding(12.dp)
                                )
                            }
                            Spacer(modifier = Modifier.height(16.dp))
                        }

                        // 1. Login (Username) maydoni
                        Text(
                            text = "Login (Foydalanuvchi nomi):",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = Color(0xFF94A3B8),
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        OutlinedTextField(
                            value = usernameInput,
                            onValueChange = { 
                                usernameInput = it
                                loginError = null
                            },
                            placeholder = { Text("Masalan: kadr_urgu yoki admin", color = Color(0xFF64748B), fontSize = 13.sp) },
                            singleLine = true,
                            shape = RoundedCornerShape(14.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = Color(0xFF0F1E3D),
                                unfocusedContainerColor = Color(0xFF0F1E3D),
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = cyanAccent,
                                unfocusedBorderColor = Color(0xFF1E3A6D)
                            ),
                            modifier = Modifier.fillMaxWidth()
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        // 2. Parol maydoni
                        Text(
                            text = "Maxfiy Parol:",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = Color(0xFF94A3B8),
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        OutlinedTextField(
                            value = passwordInput,
                            onValueChange = { 
                                passwordInput = it
                                loginError = null
                            },
                            placeholder = { Text("Parolingizni kiriting", color = Color(0xFF64748B), fontSize = 13.sp) },
                            singleLine = true,
                            visualTransformation = if (isPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            trailingIcon = {
                                IconButton(onClick = { isPasswordVisible = !isPasswordVisible }) {
                                    Text(
                                        text = if (isPasswordVisible) "👁️" else "🙈",
                                        fontSize = 14.sp
                                    )
                                }
                            },
                            shape = RoundedCornerShape(14.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = Color(0xFF0F1E3D),
                                unfocusedContainerColor = Color(0xFF0F1E3D),
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = cyanAccent,
                                unfocusedBorderColor = Color(0xFF1E3A6D)
                            ),
                            modifier = Modifier.fillMaxWidth()
                        )

                        Spacer(modifier = Modifier.height(26.dp))

                        // 3. Tizimga Kirish tugmasi
                        Button(
                            onClick = {
                                if (usernameInput.trim().isEmpty() || passwordInput.trim().isEmpty()) {
                                    loginError = "Login va parolni to'liq kiriting!"
                                    return@Button
                                }

                                isLoggingIn = true
                                loginError = null

                                scope.launch {
                                    val result = performLogin(serverUrl, usernameInput.trim(), passwordInput.trim())
                                    isLoggingIn = false

                                    if (result.isSuccess) {
                                        val data = result.getOrNull()!!
                                        val token = data.optString("token")
                                        val userObj = data.optJSONObject("user")?.toString() ?: "{}"
                                        val orgObj = data.optJSONObject("organization")?.toString() ?: "{}"

                                        prefs.edit()
                                            .putString("auth_token", token)
                                            .putString("auth_user", userObj)
                                            .putString("auth_org", orgObj)
                                            .apply()

                                        authToken = token
                                        authUserJson = userObj
                                        authOrgJson = orgObj
                                    } else {
                                        loginError = result.exceptionOrNull()?.message ?: "Login yoki parol noto'g'ri!"
                                    }
                                }
                            },
                            enabled = !isLoggingIn,
                            colors = ButtonDefaults.buttonColors(containerColor = primaryBlue),
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(52.dp)
                        ) {
                            if (isLoggingIn) {
                                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp), strokeWidth = 2.5.dp)
                            } else {
                                Text(
                                    text = "🚀 Tizimga Kirish",
                                    fontSize = 16.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(18.dp))

                        // Server sozlamalari tugmasi
                        TextButton(
                            onClick = {
                                tempServerUrl = serverUrl
                                showServerDialog = true
                            }
                        ) {
                            Text(
                                text = "⚙️ Server: ${if (serverUrl.contains("10.70.7.144")) "Mahalliy (10.70.7.144)" else "Bulutli (Cloud)"}",
                                fontSize = 12.sp,
                                color = Color(0xFF64748B),
                                fontWeight = FontWeight.Medium
                            )
                        }

                        // Server Manzili Dialog oynasi
                        if (showServerDialog) {
                            AlertDialog(
                                onDismissRequest = { showServerDialog = false },
                                title = {
                                    Text(
                                        text = "🌐 Server Manzilini Tanlash",
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 16.sp,
                                        color = Color.White
                                    )
                                },
                                text = {
                                    Column(modifier = Modifier.fillMaxWidth()) {
                                        Text(
                                            text = "Server manzili (URL):",
                                            fontSize = 12.sp,
                                            color = Color(0xFF94A3B8)
                                        )
                                        Spacer(modifier = Modifier.height(6.dp))
                                        OutlinedTextField(
                                            value = tempServerUrl,
                                            onValueChange = { tempServerUrl = it },
                                            singleLine = true,
                                            colors = OutlinedTextFieldDefaults.colors(
                                                focusedContainerColor = Color(0xFF0F1E3D),
                                                unfocusedContainerColor = Color(0xFF0F1E3D),
                                                focusedTextColor = Color.White,
                                                unfocusedTextColor = Color.White,
                                                focusedBorderColor = cyanAccent,
                                                unfocusedBorderColor = Color(0xFF1E3A6D)
                                            ),
                                            shape = RoundedCornerShape(10.dp),
                                            modifier = Modifier.fillMaxWidth()
                                        )
                                        Spacer(modifier = Modifier.height(14.dp))
                                        Text(
                                            text = "Tezkor tanlov:",
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = Color(0xFF64748B)
                                        )
                                        Spacer(modifier = Modifier.height(6.dp))
                                        Row(
                                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                                            modifier = Modifier.fillMaxWidth()
                                        ) {
                                            OutlinedButton(
                                                onClick = { tempServerUrl = defaultLocalUrl },
                                                modifier = Modifier.weight(1f),
                                                shape = RoundedCornerShape(10.dp)
                                            ) {
                                                Text("🏢 Wi-Fi", fontSize = 11.sp)
                                            }
                                            OutlinedButton(
                                                onClick = { tempServerUrl = defaultServerUrl },
                                                modifier = Modifier.weight(1f),
                                                shape = RoundedCornerShape(10.dp)
                                            ) {
                                                Text("☁️ Bulut", fontSize = 11.sp)
                                            }
                                        }
                                    }
                                },
                                confirmButton = {
                                    Button(
                                        onClick = {
                                            val cleaned = tempServerUrl.trim().removeSuffix("/")
                                            if (cleaned.isNotEmpty()) {
                                                serverUrl = cleaned
                                                prefs.edit().putString("server_url", cleaned).apply()
                                            }
                                            showServerDialog = false
                                        },
                                        colors = ButtonDefaults.buttonColors(containerColor = primaryBlue),
                                        shape = RoundedCornerShape(10.dp)
                                    ) {
                                        Text("Saqlash")
                                    }
                                },
                                dismissButton = {
                                    TextButton(onClick = { showServerDialog = false }) {
                                        Text("Bekor qilish", color = Color(0xFF94A3B8))
                                    }
                                },
                                containerColor = Color(0xFF0C162C),
                                shape = RoundedCornerShape(20.dp)
                            )
                        }
                    }
                }

            }
        }
    }

    // Serverga login so'rovini yuborish
    private suspend fun performLogin(server: String, user: String, pass: String): Result<JSONObject> = withContext(Dispatchers.IO) {
        try {
            val endpoint = server.removeSuffix("/") + "/api/v1/auth/login"
            val url = URL(endpoint)
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 12000
                readTimeout = 15000
                doOutput = true
                doInput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
            }

            val body = JSONObject().apply {
                put("username", user)
                put("password", pass)
                put("app_type", "android")
            }.toString()

            conn.outputStream.use { os ->
                os.write(body.toByteArray(Charsets.UTF_8))
            }

            val statusCode = conn.responseCode
            if (statusCode in 200..299) {
                val resp = conn.inputStream.bufferedReader().use { it.readText() }
                Result.success(JSONObject(resp))
            } else {
                val err = conn.errorStream?.bufferedReader()?.use { it.readText() } ?: ""
                var detail = "Login yoki parol noto'g'ri!"
                try {
                    val errJson = JSONObject(err)
                    if (errJson.has("detail")) {
                        detail = errJson.getString("detail")
                    }
                } catch (_: Exception) {}
                Result.failure(Exception(detail))
            }
        } catch (e: Exception) {
            Result.failure(Exception("Server bilan aloqa o'rnatib bo'lmadi! Internet yoki serveringizni tekshiring."))
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView?.canGoBack() == true) {
            webView?.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
