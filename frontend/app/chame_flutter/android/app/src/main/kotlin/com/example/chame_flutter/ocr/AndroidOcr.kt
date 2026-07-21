package com.chame.kasse.ocr

import android.content.Context
import android.graphics.Rect
import android.net.Uri
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.Text
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import kotlin.math.abs

class AndroidOcr(
    private val context: Context
) {
    private val recognizer = TextRecognition.getClient(
        TextRecognizerOptions.DEFAULT_OPTIONS
    )

    /**
     * How close (as a fraction of an element's own height) two elements'
     * vertical centers must be to be considered part of the same row.
     * Only the y-axis is used for grouping so a row can span the full
     * width of the receipt (e.g. product name on the left, price on the
     * right) even though ML Kit's own block/line detection would split
     * them apart based on horizontal gaps.
     */
    private val rowYOverlapTolerance = 0.5

    fun recognizeFile(
        imagePath: String,
        onSuccess: (String) -> Unit,
        onError: (Throwable) -> Unit
    ) {
        try {
            val file = File(imagePath)

            if (!file.exists()) {
                onError(
                    IllegalArgumentException(
                        "Image file does not exist: $imagePath"
                    )
                )
                return
            }

            if (!file.isFile) {
                onError(
                    IllegalArgumentException(
                        "Image path is not a file: $imagePath"
                    )
                )
                return
            }

            val image = InputImage.fromFilePath(
                context,
                Uri.fromFile(file)
            )

            recognizer.process(image)
                .addOnSuccessListener { recognizedText ->
                    try {
                        val response = JSONObject().apply {
                            put("text", recognizedText.text)
                            // Row-grouped output (y-only clustering) is what the
                            // Python side should parse; raw text is kept above
                            // only for debugging/display.
                            put("rows", buildRowsJson(recognizedText))
                        }

                        onSuccess(response.toString())
                    } catch (error: Throwable) {
                        onError(error)
                    }
                }
                .addOnFailureListener { error ->
                    onError(error)
                }
        } catch (error: Throwable) {
            onError(error)
        }
    }

    private data class ElementInfo(
        val text: String,
        val confidence: Float?,
        val boundingBox: Rect?
    )

    /**
     * Flattens every recognized element (ignoring ML Kit's own block/line
     * grouping) and re-groups them into rows using only vertical overlap.
     * Within each row, elements are ordered left-to-right purely for
     * readability; x position never affects which row an element belongs to.
     */
    private fun buildRowsJson(recognizedText: Text): JSONArray {
        val elements = mutableListOf<ElementInfo>()
        for (block in recognizedText.textBlocks) {
            for (line in block.lines) {
                for (element in line.elements) {
                    elements.add(
                        ElementInfo(
                            text = element.text,
                            confidence = element.confidence,
                            boundingBox = element.boundingBox
                        )
                    )
                }
            }
        }

        // Process top-to-bottom so rows are formed in reading order.
        elements.sortBy { it.boundingBox?.top ?: 0 }

        val rows = mutableListOf<MutableList<ElementInfo>>()
        val rowCenters = mutableListOf<Double>()

        for (element in elements) {
            val box = element.boundingBox
            if (box == null) {
                // No position info available: give it its own row rather
                // than guessing which row it belongs to.
                rows.add(mutableListOf(element))
                rowCenters.add(Double.NaN)
                continue
            }

            val centerY = (box.top + box.bottom) / 2.0
            val height = (box.bottom - box.top).coerceAtLeast(1).toDouble()

            val matchedRowIndex = rowCenters.indexOfFirst { center ->
                !center.isNaN() && abs(centerY - center) < height * rowYOverlapTolerance
            }

            if (matchedRowIndex == -1) {
                rows.add(mutableListOf(element))
                rowCenters.add(centerY)
            } else {
                rows[matchedRowIndex].add(element)
                // Recompute the row's average center so later elements are
                // compared against the whole row, not just its first element.
                rowCenters[matchedRowIndex] = rows[matchedRowIndex]
                    .mapNotNull { it.boundingBox }
                    .map { (it.top + it.bottom) / 2.0 }
                    .average()
            }
        }

        // Guarantee top-to-bottom ordering in the output.
        rows.sortBy { row ->
            row.mapNotNull { it.boundingBox }.map { it.top }.average()
        }

        val rowsJson = JSONArray()
        for (row in rows) {
            val orderedRow = row.sortedBy { it.boundingBox?.left ?: 0 }

            val elementsJson = JSONArray()
            for (element in orderedRow) {
                elementsJson.put(
                    JSONObject().apply {
                        put("text", element.text)
                        putNullableConfidence("confidence", element.confidence)
                        putBoundingBox(element.boundingBox)
                    }
                )
            }

            rowsJson.put(
                JSONObject().apply {
                    put("text", orderedRow.joinToString(" ") { it.text })
                    putBoundingBox(mergeBoundingBoxes(orderedRow.mapNotNull { it.boundingBox }))
                    put("elements", elementsJson)
                }
            )
        }

        return rowsJson
    }

    private fun mergeBoundingBoxes(boxes: List<Rect>): Rect? {
        if (boxes.isEmpty()) return null
        val merged = Rect(boxes.first())
        for (box in boxes.drop(1)) {
            merged.union(box)
        }
        return merged
    }

    private fun JSONObject.putBoundingBox(
        boundingBox: Rect?
    ) {
        if (boundingBox == null) {
            put("bounding_box", JSONObject.NULL)
            return
        }

        put(
            "bounding_box",
            JSONObject().apply {
                put("left", boundingBox.left)
                put("top", boundingBox.top)
                put("right", boundingBox.right)
                put("bottom", boundingBox.bottom)
                put("width", boundingBox.width())
                put("height", boundingBox.height())
            }
        )
    }

    private fun JSONObject.putNullableConfidence(
        key: String,
        confidence: Float?
    ) {
        if (confidence == null) {
            put(key, JSONObject.NULL)
        } else {
            put(key, confidence.toDouble())
        }
    }

    fun close() {
        recognizer.close()
    }
}