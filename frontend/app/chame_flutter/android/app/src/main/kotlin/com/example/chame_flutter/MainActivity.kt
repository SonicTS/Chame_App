package com.chame.kasse

import androidx.annotation.NonNull
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : FlutterActivity() {

    private val CHANNEL = "samples.flutter.dev/chame/python"

    override fun configureFlutterEngine(@NonNull flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Start Python once per process
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        val py = Python.getInstance()

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        ).setMethodCallHandler { call, result ->

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
                
                else -> result.notImplemented()
            }
            
        }
    }
}