package com.chame.kasse

import androidx.annotation.NonNull
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date

class MainActivity : FlutterActivity() {

    private val CHANNEL = "samples.flutter.dev/chame/python"
    private var flutterMethodChannel: MethodChannel? = null
    
    // File picker constants and state
    private val FILE_PICK_REQUEST_CODE = 12345
    private var pendingFilePickResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(@NonNull flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Start Python once per process
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        val py = Python.getInstance()
        
        // Set environment variable to indicate Flutter environment for logging
        try {
            val os = py.getModule("os")
            os?.get("environ")?.callAttr("__setitem__", "FLUTTER_ENV", "true")
            
            // Set up activity reference for the firebase logger
            val main = py.getModule("__main__")
            main?.put("activity", this)
        } catch (e: Exception) {
            android.util.Log.w("MainActivity", "Failed to set FLUTTER_ENV or activity: ${e.message}")
        }

        // Store reference to the method channel for reverse calls
        flutterMethodChannel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        )

        flutterMethodChannel?.setMethodCallHandler { call, result ->

            when (call.method) {
                "ping" -> {
                    // ── Module ────────────────────────────────────────────────
                    val module = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module services.admin_api not found", null
                        )

                    try {
                        module.callAttr("create_database")
                        val pyResult = module.callAttr("get_bank")
                        result.success("pong from Python $pyResult")
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }

                    
                }
                "get_all_ingredients" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_all_ingredients")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "add_ingredient" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val name = call.argument<String>("name")
                        val pricePerPackage = call.argument<Number>("price_per_package")
                        val stockQuantity = call.argument<Number>("stock_quantity")
                        val numberIngredients = call.argument<Number>("number_ingredients")
                        val pfand = call.argument<Number>("pfand") ?: 0 // Default to 0 if not provided
                        if (name == null || pricePerPackage == null || stockQuantity == null || numberIngredients == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for add_ingredient", null)
                            return@setMethodCallHandler
                        }
                        val pyResult = pyModule.callAttr(
                            "add_ingredient",
                            name,
                            pricePerPackage.toDouble(),
                            stockQuantity.toInt(),
                            numberIngredients.toInt(),
                            pfand.toDouble()
                        )
                        result.success(null) // Success, no error message
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "add_user" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val name = call.argument<String>("name")
                        val balance = call.argument<Number>("balance")
                        val role = call.argument<String>("role")
                        var password = call.argument<String>("password")
                        if (password == null) {
                            password = "" // Set a default password if none provided
                        }
                        if (name == null || balance == null || role == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for add_user", null)
                            return@setMethodCallHandler
                        }
                        val pyResult = pyModule.callAttr(
                            "add_user",
                            name,
                            balance.toDouble(),
                            role,
                            password
                        )
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "withdraw" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        val amount = call.argument<Number>("amount")
                        if (userId == null || amount == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for withdraw", null)
                            return@setMethodCallHandler
                        }
                        pyModule.callAttr("withdraw", userId.toInt(), amount.toDouble())
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "deposit" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        val amount = call.argument<Number>("amount")
                        if (userId == null || amount == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for deposit", null)
                            return@setMethodCallHandler
                        }
                        pyModule.callAttr("deposit", userId.toInt(), amount.toDouble())
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "add_product" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val name = call.argument<String>("name")
                        val category = call.argument<String>("category")
                        val price = call.argument<Number>("price")
                        val ingredientsIds = call.argument<List<Number>>("ingredients_ids")
                        val quantities = call.argument<List<Number>>("quantities")
                        val toasterSpace = call.argument<Number>("toaster_space")
                        if (name == null || category == null || price == null || ingredientsIds == null || quantities == null || toasterSpace == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for add_product", null)
                            return@setMethodCallHandler
                        }
                        pyModule.callAttr(
                            "add_product",
                            name,
                            category,
                            price.toDouble(),
                            ingredientsIds.map { it.toInt() }.toTypedArray(),
                            quantities.map { it.toDouble() }.toTypedArray(),
                            toasterSpace.toInt()
                        )
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "restock_ingredient" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val ingredientId = call.argument<Number>("ingredient_id")
                        val quantity = call.argument<Number>("quantity")
                        if (ingredientId == null || quantity == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for restock_ingredient", null)
                            return@setMethodCallHandler
                        }
                        pyModule.callAttr("restock_ingredient", ingredientId.toInt(), quantity.toInt())
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "make_purchase" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        val productId = call.argument<Number>("product_id")
                        val quantity = call.argument<Number>("quantity")
                        if (userId == null || productId == null || quantity == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for make_purchase", null)
                            return@setMethodCallHandler
                        }
                        pyModule.callAttr("make_purchase", userId.toInt(), productId.toInt(), quantity.toInt())
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "add_toast_round" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val productIds = call.argument<List<Number>>("product_ids")
                        val consumerSelections = call.argument<List<Number>>("consumer_selections")
                        val donatorSelections = call.argument<List<Number>>("donator_selections")
                        if (productIds == null || consumerSelections == null || donatorSelections == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for add_toast_round", null)
                            return@setMethodCallHandler
                        }
                        pyModule.callAttr(
                            "add_toast_round",
                            productIds.map { it.toInt() }.toTypedArray(),
                            consumerSelections.map { it.toInt() }.toTypedArray(),
                            donatorSelections.map { it.toInt() }.toTypedArray()
                        )
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "bank_withdraw" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val amount = call.argument<Number>("amount")
                        val description = call.argument<String>("description")
                        if (amount == null || description == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for bank_withdraw", null)
                            return@setMethodCallHandler
                        }
                        pyModule.callAttr("bank_withdraw", amount.toDouble(), description)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_all_users" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_all_users")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_all_products" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_all_products")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_all_sales" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_all_sales")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_all_toast_products" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_all_toast_products")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_all_raw_products" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_all_raw_products")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_all_toast_rounds" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_all_toast_rounds")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_filtered_transaction" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Any>("user_id")
                        val txType = call.argument<String>("tx_type")
                        val pyResult = if (userId != null && txType != null) {
                            pyModule.callAttr("get_filtered_transaction", userId, txType)
                        } else {
                            pyModule.callAttr("get_filtered_transaction")
                        }
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_bank" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_bank")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_bank_transaction" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_bank_transaction")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "restock_ingredients" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val restocksJson = call.argument<String>("restocks")
                        if (restocksJson == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for restock_ingredients", null)
                            return@setMethodCallHandler
                        }
                        val json = py.getModule("json")
                        val restocksList = json.callAttr("loads", restocksJson)
                        // Each item: {"id": ..., "restock": ...}
                        pyModule.callAttr("restock_ingredients", restocksList)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "update_stock" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val ingredientId = call.argument<Number>("ingredient_id")
                        val amount = call.argument<Number>("amount")
                        val comment = call.argument<String>("comment") ?: ""
                        
                        if (ingredientId == null || amount == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for update_stock", null)
                            return@setMethodCallHandler
                        }
                        
                        pyModule.callAttr("update_stock", ingredientId.toInt(), amount.toInt(), comment)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "get_stock_history" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val ingredientId = call.argument<Number>("ingredient_id")
                        
                        if (ingredientId == null) {
                            result.error("ARGUMENT_ERROR", "Missing ingredient_id for get_stock_history", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("get_stock_history", ingredientId.toInt())
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "get_all_stock_history" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_all_stock_history")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "login" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val user = call.argument<String>("user")
                        val password = call.argument<String>("password")
                        if (user == null || password == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for login", null)
                            return@setMethodCallHandler
                        }
                        val pyResult = pyModule.callAttr("login", user, password)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "change_password" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val user_id = call.argument<Integer>("user_id")
                        val oldPassword = call.argument<String>("old_password")
                        val newPassword = call.argument<String>("new_password")
                        if (oldPassword == null || newPassword == null || user_id == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for change_password", null)
                            return@setMethodCallHandler
                        }
                        pyModule.callAttr("change_password", user_id, oldPassword, newPassword)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "submit_pfand_return" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        val product_json = call.argument<String>("product_list")
                        if (userId == null || product_json == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for submit_pfand_return", null)
                            return@setMethodCallHandler
                        }
                        val json = py.getModule("json")
                        val productList = json.callAttr("loads", product_json)
                        pyModule.callAttr("submit_pfand_return", userId.toInt(), productList)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_pfand_history" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("get_pfand_history")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                // ========== BACKUP MANAGEMENT ROUTES ==========
                "create_backup" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val backupType = call.argument<String>("backup_type") ?: "manual"
                        val description = call.argument<String>("description") ?: ""
                        val createdBy = call.argument<String>("created_by") ?: "android_app"
                        
                        val pyResult = pyModule.callAttr("create_backup", backupType, description, createdBy)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "list_backups" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val pyResult = pyModule.callAttr("list_backups")
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "restore_backup" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val backupPath = call.argument<String>("backup_path")
                        val confirm = call.argument<Boolean>("confirm") ?: false
                        
                        if (backupPath == null) {
                            result.error("ARGUMENT_ERROR", "Missing backup_path argument for restore_backup", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("restore_backup", backupPath, confirm)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "delete_backup" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val backupFilename = call.argument<String>("backup_filename")
                        
                        if (backupFilename == null) {
                            result.error("ARGUMENT_ERROR", "Missing backup_filename argument for delete_backup", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("delete_backup", backupFilename)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "export_backup_to_public" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val backupFilename = call.argument<String>("backup_filename")
                        
                        if (backupFilename == null) {
                            result.error("ARGUMENT_ERROR", "Missing backup_filename argument for export_backup_to_public", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("export_backup_to_public", backupFilename)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "upload_backup_to_server" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val backupFilename = call.argument<String>("backup_filename")
                        val serverConfigJson = call.argument<String>("server_config")
                        
                        if (backupFilename == null || serverConfigJson == null) {
                            result.error("ARGUMENT_ERROR", "Missing backup_filename or server_config argument for upload_backup_to_server", null)
                            return@setMethodCallHandler
                        }
                        
                        // Parse server config JSON in Python
                        val serverConfig = py.getModule("json").callAttr("loads", serverConfigJson)
                        val pyResult = pyModule.callAttr("upload_backup_to_server", backupFilename, serverConfig)
                        
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "download_backup_from_server" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val remoteFilename = call.argument<String>("remote_filename")
                        val serverConfigJson = call.argument<String>("server_config")
                        
                        if (remoteFilename == null || serverConfigJson == null) {
                            result.error("ARGUMENT_ERROR", "Missing remote_filename or server_config argument for download_backup_from_server", null)
                            return@setMethodCallHandler
                        }
                        
                        // Parse server config JSON in Python
                        val serverConfig = py.getModule("json").callAttr("loads", serverConfigJson)
                        val pyResult = pyModule.callAttr("download_backup_from_server", serverConfig, remoteFilename)
                        
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "import_backup_from_share" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val sharedFilePath = call.argument<String>("shared_file_path")
                        
                        if (sharedFilePath == null) {
                            result.error("ARGUMENT_ERROR", "Missing shared_file_path argument for import_backup_from_share", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("import_backup_from_share", sharedFilePath)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "pick_file_for_import" -> {
                    // Launch file picker for backup import
                    try {
                        val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                            type = "*/*"
                            putExtra(Intent.EXTRA_MIME_TYPES, arrayOf(
                                "application/octet-stream",
                                "application/x-sqlite3",
                                "application/vnd.sqlite3",
                                "*/*"
                            ))
                            addCategory(Intent.CATEGORY_OPENABLE)
                        }
                        
                        pendingFilePickResult = result
                        startActivityForResult(Intent.createChooser(intent, "Select Backup File"), FILE_PICK_REQUEST_CODE)
                        
                    } catch (e: Exception) {
                        result.error("FILE_PICKER_ERROR", "Failed to open file picker: ${e.localizedMessage}", null)
                    }
                }
                
                "list_server_backups" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val serverConfigJson = call.argument<String>("server_config")
                        
                        if (serverConfigJson == null) {
                            result.error("ARGUMENT_ERROR", "Missing server_config argument for list_server_backups", null)
                            return@setMethodCallHandler
                        }
                        
                        // Parse server config JSON in Python
                        val serverConfig = py.getModule("json").callAttr("loads", serverConfigJson)
                        val pyResult = pyModule.callAttr("list_server_backups", serverConfig)
                        
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                // ========== DELETION MANAGEMENT ROUTES ==========
                "check_deletion_dependencies" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val entityType = call.argument<String>("entity_type")
                        val entityId = call.argument<Number>("entity_id")
                        
                        if (entityType == null || entityId == null) {
                            result.error("ARGUMENT_ERROR", "Missing entity_type or entity_id for check_deletion_dependencies", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("check_deletion_dependencies", entityType, entityId.toInt())
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "safe_delete_user" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        val force = call.argument<Boolean>("force") ?: false
                        
                        if (userId == null) {
                            result.error("ARGUMENT_ERROR", "Missing user_id for safe_delete_user", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("safe_delete_user", userId.toInt(), force)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "safe_delete_product" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val productId = call.argument<Number>("product_id")
                        val force = call.argument<Boolean>("force") ?: false
                        
                        if (productId == null) {
                            result.error("ARGUMENT_ERROR", "Missing product_id for safe_delete_product", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("safe_delete_product", productId.toInt(), force)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "safe_delete_ingredient" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val ingredientId = call.argument<Number>("ingredient_id")
                        val force = call.argument<Boolean>("force") ?: false
                        
                        if (ingredientId == null) {
                            result.error("ARGUMENT_ERROR", "Missing ingredient_id for safe_delete_ingredient", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("safe_delete_ingredient", ingredientId.toInt(), force)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "delete_sale_record" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val saleId = call.argument<Number>("sale_id")
                        val adminUserId = call.argument<Number>("admin_user_id")
                        
                        if (saleId == null || adminUserId == null) {
                            result.error("ARGUMENT_ERROR", "Missing sale_id or admin_user_id for delete_sale_record", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("delete_sale_record", saleId.toInt(), adminUserId.toInt())
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                            result.success(jsonString)
                        }
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "change_user_role" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        val newRole = call.argument<String>("new_role")
                        
                        if (userId == null || newRole == null) {
                            result.error("ARGUMENT_ERROR", "Missing user_id or new_role for change_user_role", null)
                            return@setMethodCallHandler
                        }
                        
                        pyModule.callAttr("change_user_role", userId.toInt(), newRole)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "soft_delete_user" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        val deletedBy = call.argument<String>("deleted_by") ?: "admin"
                        
                        if (userId == null) {
                            result.error("ARGUMENT_ERROR", "Missing user_id for soft_delete_user", null)
                            return@setMethodCallHandler
                        }
                        
                        pyModule.callAttr("soft_delete_user", userId.toInt(), deletedBy)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "soft_delete_product" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val productId = call.argument<Number>("product_id")
                        val deletedBy = call.argument<String>("deleted_by") ?: "admin"
                        
                        if (productId == null) {
                            result.error("ARGUMENT_ERROR", "Missing product_id for soft_delete_product", null)
                            return@setMethodCallHandler
                        }
                        
                        pyModule.callAttr("soft_delete_product", productId.toInt(), deletedBy)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "soft_delete_ingredient" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val ingredientId = call.argument<Number>("ingredient_id")
                        val deletedBy = call.argument<String>("deleted_by") ?: "admin"
                        
                        if (ingredientId == null) {
                            result.error("ARGUMENT_ERROR", "Missing ingredient_id for soft_delete_ingredient", null)
                            return@setMethodCallHandler
                        }
                        
                        pyModule.callAttr("soft_delete_ingredient", ingredientId.toInt(), deletedBy)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "restore_user" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        
                        if (userId == null) {
                            result.error("ARGUMENT_ERROR", "Missing user_id for restore_user", null)
                            return@setMethodCallHandler
                        }
                        
                        pyModule.callAttr("restore_user", userId.toInt())
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "restore_product" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val productId = call.argument<Number>("product_id")
                        
                        if (productId == null) {
                            result.error("ARGUMENT_ERROR", "Missing product_id for restore_product", null)
                            return@setMethodCallHandler
                        }
                        
                        pyModule.callAttr("restore_product", productId.toInt())
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                "restore_ingredient" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val ingredientId = call.argument<Number>("ingredient_id")
                        
                        if (ingredientId == null) {
                            result.error("ARGUMENT_ERROR", "Missing ingredient_id for restore_ingredient", null)
                            return@setMethodCallHandler
                        }
                        
                        pyModule.callAttr("restore_ingredient", ingredientId.toInt())
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }

                "get_deleted_users" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val deletedUsers = pyModule.callAttr("get_deleted_users")
                        val jsonString = py.getModule("json").callAttr("dumps", deletedUsers).toString()
                        result.success(jsonString)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }

                "get_deleted_products" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val deletedProducts = pyModule.callAttr("get_deleted_products")
                        val jsonString = py.getModule("json").callAttr("dumps", deletedProducts).toString()
                        result.success(jsonString)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }

                "get_deleted_ingredients" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val deletedIngredients = pyModule.callAttr("get_deleted_ingredients")
                        val jsonString = py.getModule("json").callAttr("dumps", deletedIngredients).toString()
                        result.success(jsonString)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "enhanced_delete_user" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val userId = call.argument<Number>("user_id")
                        val deletedByUser = call.argument<String>("deleted_by_user") ?: "admin"
                        val hardDelete = call.argument<Boolean>("hard_delete") ?: false
                        val cascadeChoicesJson = call.argument<String>("cascade_choices") ?: "{}"
                        
                        if (userId == null) {
                            result.error("ARGUMENT_ERROR", "Missing user_id for enhanced_delete_user", null)
                            return@setMethodCallHandler
                        }
                        
                        val json = py.getModule("json")
                        val cascadeChoices = json.callAttr("loads", cascadeChoicesJson)
                        
                        val pyResult = pyModule.callAttr("enhanced_delete_user", userId.toInt(), deletedByUser, hardDelete, cascadeChoices)
                        val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                        result.success(jsonString)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "enhanced_delete_product" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val productId = call.argument<Number>("product_id")
                        val deletedByUser = call.argument<String>("deleted_by_user") ?: "admin"
                        val hardDelete = call.argument<Boolean>("hard_delete") ?: false
                        val cascadeChoicesJson = call.argument<String>("cascade_choices") ?: "{}"
                        
                        if (productId == null) {
                            result.error("ARGUMENT_ERROR", "Missing product_id for enhanced_delete_product", null)
                            return@setMethodCallHandler
                        }
                        
                        val json = py.getModule("json")
                        val cascadeChoices = json.callAttr("loads", cascadeChoicesJson)
                        
                        val pyResult = pyModule.callAttr("enhanced_delete_product", productId.toInt(), deletedByUser, hardDelete, cascadeChoices)
                        val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                        result.success(jsonString)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "enhanced_delete_ingredient" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val ingredientId = call.argument<Number>("ingredient_id")
                        val deletedByUser = call.argument<String>("deleted_by_user") ?: "admin"
                        val hardDelete = call.argument<Boolean>("hard_delete") ?: false
                        val cascadeChoicesJson = call.argument<String>("cascade_choices") ?: "{}"
                        
                        if (ingredientId == null) {
                            result.error("ARGUMENT_ERROR", "Missing ingredient_id for enhanced_delete_ingredient", null)
                            return@setMethodCallHandler
                        }
                        
                        val json = py.getModule("json")
                        val cascadeChoices = json.callAttr("loads", cascadeChoicesJson)
                        
                        val pyResult = pyModule.callAttr("enhanced_delete_ingredient", ingredientId.toInt(), deletedByUser, hardDelete, cascadeChoices)
                        val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                        result.success(jsonString)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                "get_deletion_impact_analysis" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val entityType = call.argument<String>("entity_type")
                        val entityId = call.argument<Number>("entity_id")
                        if (entityType == null || entityId == null) {
                            result.error("ARGUMENT_ERROR", "Missing entity_type or entity_id for get_deletion_impact_analysis", null)
                            return@setMethodCallHandler
                        }
                        val pyResult = pyModule.callAttr("get_deletion_impact_analysis", entityType, entityId.toInt())
                        val jsonString = py.getModule("json").callAttr("dumps", pyResult).toString()
                        result.success(jsonString)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                
                // ========== NEW SIMPLIFIED DELETION SYSTEM ==========
                "analyze_deletion_impact" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val entityType = call.argument<String>("entity_type")
                        val entityId = call.argument<Number>("entity_id")
                        
                        if (entityType == null || entityId == null) {
                            result.error("ARGUMENT_ERROR", "Missing entity_type or entity_id for analyze_deletion_impact", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("analyze_deletion_impact", entityType, entityId.toInt())
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            result.success(pyResult.toString())
                        }
                    } catch (e: Exception) {
                        result.error("ANALYZE_ERROR", "Failed to analyze deletion impact: ${e.localizedMessage}", null)
                    }
                }
                
                "execute_deletion" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val entityType = call.argument<String>("entity_type")
                        val entityId = call.argument<Number>("entity_id")
                        val deletedBy = call.argument<String>("deleted_by") ?: "flutter_admin"
                        
                        if (entityType == null || entityId == null) {
                            result.error("ARGUMENT_ERROR", "Missing entity_type or entity_id for execute_deletion", null)
                            return@setMethodCallHandler
                        }
                        
                        val pyResult = pyModule.callAttr("execute_deletion", entityType, entityId.toInt(), deletedBy)
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            result.success(pyResult.toString())
                        }
                    } catch (e: Exception) {
                        result.error("DELETE_ERROR", "Failed to execute deletion: ${e.localizedMessage}", null)
                    }
                }
                
                "test_firebase_logging" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        println("🧪 [ANDROID] Starting Firebase logging test from Android/Kotlin...")
                        val pyResult = pyModule.callAttr("test_firebase_logging")
                        
                        // Also test the reverse bridge
                        println("🔄 [ANDROID] Testing reverse bridge call...")
                        logToFirebase("INFO", "🧪 Test from Android MainActivity", mapOf(
                            "test_type" to "android_kotlin_test",
                            "source" to "MainActivity.kt",
                            "timestamp" to System.currentTimeMillis().toString()
                        ))
                        
                        if (pyResult == null) {
                            result.success("null")
                        } else {
                            result.success(pyResult.toString())
                        }
                        println("✅ [ANDROID] Firebase logging test completed successfully")
                    } catch (e: Exception) {
                        println("❌ [ANDROID] Firebase logging test failed: ${e.localizedMessage}")
                        result.error("FIREBASE_TEST_ERROR", "Firebase test failed: ${e.localizedMessage}", null)
                    }
                }
                
                "share_file" -> {
                    try {
                        val filePath = call.argument<String>("file_path")
                        val title = call.argument<String>("title") ?: "Share Backup"
                        
                        if (filePath == null) {
                            result.error("ARGUMENT_ERROR", "Missing file_path argument for share_file", null)
                            return@setMethodCallHandler
                        }
                        
                        shareFile(filePath, title)
                        result.success("File shared successfully")
                    } catch (e: Exception) {
                        result.error("SHARE_ERROR", e.localizedMessage, null)
                    }
                }
                
                "make_multiple_purchases" -> {
                    val pyModule = py.getModule("services.admin_api")
                        ?: return@setMethodCallHandler result.error(
                            "PY_MODULE", "Module admin_api not found", null
                        )
                    try {
                        val itemListJson = call.argument<String>("item_list")
                        if (itemListJson == null) {
                            result.error("ARGUMENT_ERROR", "Missing argument for make_multiple_purchases", null)
                            return@setMethodCallHandler
                        }
                        
                        // Parse JSON to Python object
                        val jsonModule = py.getModule("json")
                        val itemList = jsonModule.callAttr("loads", itemListJson)
                        
                        pyModule.callAttr("make_multiple_purchases", itemList)
                        result.success(null)
                    } catch (e: Exception) {
                        result.error("PYTHON_ERROR", e.localizedMessage, null)
                    }
                }
                else -> result.notImplemented()
            }
            
        }
    }

    // ========== REVERSE BRIDGE METHODS (Python → Flutter) ==========
    
    /**
     * Method to call Flutter from Python
     * This is called by Python code through Chaquopy
     */
    fun logToFirebase(level: String, message: String, metadata: Map<String, Any> = emptyMap()) {
        runOnUiThread {
            try {
                flutterMethodChannel?.invokeMethod("log_to_firebase", mapOf(
                    "level" to level,
                    "message" to message,
                    "metadata" to metadata
                ))
            } catch (e: Exception) {
                println("Failed to call Flutter logToFirebase: ${e.message}")
            }
        }
    }
    
    /**
     * Generic method to call any Flutter method from Python
     */
    fun callFlutterMethod(method: String, arguments: Map<String, Any> = emptyMap()) {
        runOnUiThread {
            try {
                flutterMethodChannel?.invokeMethod(method, arguments)
            } catch (e: Exception) {
                println("Failed to call Flutter method '$method': ${e.message}")
            }
        }
    }
    
    /**
     * Show progress updates from Python operations
     */
    fun updateProgress(progress: Double, message: String = "") {
        runOnUiThread {
            try {
                flutterMethodChannel?.invokeMethod("update_progress", mapOf(
                    "progress" to progress,
                    "message" to message
                ))
            } catch (e: Exception) {
                println("Failed to update progress: ${e.message}")
            }
        }
    }
    
    /**
     * Show notifications from Python
     */
    fun showNotification(title: String, message: String, type: String = "info") {
        runOnUiThread {
            try {
                flutterMethodChannel?.invokeMethod("show_notification", mapOf(
                    "title" to title,
                    "message" to message,
                    "type" to type
                ))
            } catch (e: Exception) {
                println("Failed to show notification: ${e.message}")
            }
        }
    }
    
    /**
     * Share a file using Android's built-in sharing mechanism
     */
    private fun shareFile(filePath: String, title: String) {
        try {
            val sourceFile = File(filePath)
            if (!sourceFile.exists()) {
                throw Exception("File not found: $filePath")
            }
            
            // Copy file to app's external files directory for sharing
            val externalFilesDir = getExternalFilesDir(null)
            if (externalFilesDir == null) {
                throw Exception("External files directory not available")
            }
            
            val shareDir = File(externalFilesDir, "share")
            if (!shareDir.exists()) {
                shareDir.mkdirs()
            }
            
            val shareFile = File(shareDir, sourceFile.name)
            sourceFile.copyTo(shareFile, overwrite = true)
            
            val intent = Intent(Intent.ACTION_SEND)
            intent.type = "application/octet-stream"
            
            // Use FileProvider for the copied file
            val uri: Uri = FileProvider.getUriForFile(
                this,
                "${applicationContext.packageName}.fileprovider",
                shareFile
            )
            
            intent.putExtra(Intent.EXTRA_STREAM, uri)
            intent.putExtra(Intent.EXTRA_SUBJECT, title)
            intent.putExtra(Intent.EXTRA_TEXT, "Chame database backup file exported on ${SimpleDateFormat("yyyy-MM-dd HH:mm").format(Date())}")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            
            startActivity(Intent.createChooser(intent, title))
            
            // Clean up old shared files (keep only the last 5)
            cleanupOldSharedFiles(shareDir)
            
        } catch (e: Exception) {
            println("Failed to share file: ${e.message}")
            throw e
        }
    }
    
    /**
     * Clean up old shared files to prevent storage accumulation
     */
    private fun cleanupOldSharedFiles(shareDir: File) {
        try {
            val files = shareDir.listFiles() ?: return
            val sortedFiles = files.sortedByDescending { it.lastModified() }
            
            // Keep only the 5 most recent files
            sortedFiles.drop(5).forEach { file ->
                if (file.isFile) {
                    file.delete()
                }
            }
        } catch (e: Exception) {
            println("Failed to cleanup shared files: ${e.message}")
            // Don't throw - this is not critical
        }
    }
    
    /**
     * Handle file picker results for backup import
     */
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        
        if (requestCode == FILE_PICK_REQUEST_CODE) {
            val result = pendingFilePickResult
            pendingFilePickResult = null
            
            if (result == null) {
                return
            }
            
            if (resultCode == RESULT_OK && data?.data != null) {
                try {
                    val uri = data.data!!
                    val filePath = getFilePathFromUri(uri)
                    
                    if (filePath != null) {
                        result.success(filePath)
                    } else {
                        result.error("FILE_PATH_ERROR", "Could not get file path from selected file", null)
                    }
                } catch (e: Exception) {
                    result.error("FILE_PROCESSING_ERROR", "Error processing selected file: ${e.localizedMessage}", null)
                }
            } else {
                result.error("FILE_PICKER_CANCELLED", "File selection was cancelled", null)
            }
        }
    }
    
    /**
     * Get file path from content URI for backup import
     */
    private fun getFilePathFromUri(uri: Uri): String? {
        return try {
            // For content URIs, copy to a temporary location
            if (uri.scheme == "content") {
                val inputStream = contentResolver.openInputStream(uri)
                    ?: return null
                
                // Create temp file in cache directory
                val tempDir = File(cacheDir, "backup_imports")
                tempDir.mkdirs()
                
                val fileName = getFileName(uri) ?: "backup_${System.currentTimeMillis()}.db"
                val tempFile = File(tempDir, fileName)
                
                tempFile.outputStream().use { output ->
                    inputStream.use { input ->
                        input.copyTo(output)
                    }
                }
                
                tempFile.absolutePath
            } else {
                // For file URIs, return path directly
                uri.path
            }
        } catch (e: Exception) {
            android.util.Log.e("MainActivity", "Error getting file path from URI", e)
            null
        }
    }
    
    /**
     * Get filename from content URI
     */
    private fun getFileName(uri: Uri): String? {
        return try {
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                if (nameIndex >= 0 && cursor.moveToFirst()) {
                    cursor.getString(nameIndex)
                } else {
                    null
                }
            }
        } catch (e: Exception) {
            null
        }
    }
}