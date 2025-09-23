import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity implements TextToSpeech.OnInitListener {

    private static final String JSON_URL = "https://raw.githubusercontent.com/SoWarmhome/Mercy/refs/heads/main/Dictation/Dictation.json";
    private TextToSpeech tts;
    private Map<String, List<String>> dataMap = new HashMap<>();  // 儲存解析後的數據
    private List<String> currentItems;
    private int currentIndex = 0;
    private String currentLang = "zh-CN";  // 預設普通話

    private Spinner typeSpinner, langSpinner, lessonSpinner;
    private Button startButton, repeatButton, nextButton;
    private TextView currentTextView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        typeSpinner = findViewById(R.id.type_spinner);
        langSpinner = findViewById(R.id.lang_spinner);
        lessonSpinner = findViewById(R.id.lesson_spinner);
        startButton = findViewById(R.id.start_button);
        repeatButton = findViewById(R.id.repeat_button);
        nextButton = findViewById(R.id.next_button);
        currentTextView = findViewById(R.id.current_text);

        tts = new TextToSpeech(this, this);

        // 設定類型選擇
        String[] types = {"中文詞語", "中文課文", "英文詞語", "英文課文", "常識詞語"};
        ArrayAdapter<String> typeAdapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, types);
        typeSpinner.setAdapter(typeAdapter);

        // 語言選擇（僅中文類型顯示）
        String[] langs = {"普通話", "廣東話"};
        ArrayAdapter<String> langAdapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, langs);
        langSpinner.setAdapter(langAdapter);
        langSpinner.setVisibility(View.GONE);  // 預設隱藏

        typeSpinner.setOnItemSelectedListener((parent, view, position, id) -> {
            String selectedType = types[position];
            if (selectedType.contains("英文")) {
                langSpinner.setVisibility(View.GONE);
                currentLang = "en-US";
            } else {
                langSpinner.setVisibility(View.VISIBLE);
                currentLang = "zh-CN";
            }
            // 更新課次選擇
            updateLessonSpinner(selectedType);
        });

        langSpinner.setOnItemSelectedListener((parent, view, position, id) -> {
            currentLang = position == 0 ? "zh-CN" : "zh-HK";
        });

        startButton.setOnClickListener(v -> startDictation());

        // 下載 JSON
        new Thread(this::downloadAndParseJson).start();
    }

    private void downloadAndParseJson() {
        OkHttpClient client = new OkHttpClient();
        Request request = new Request.Builder().url(JSON_URL).build();
        try {
            Response response = client.newCall(request).execute();
            if (response.isSuccessful()) {
                String jsonData = response.body().string();
                JSONObject jsonObject = new JSONObject(jsonData);

                // 解析 JSON（調整為您的結構）
                Iterator<String> keys = jsonObject.keys();
                while (keys.hasNext()) {
                    String key = keys.next();
                    JSONArray array = jsonObject.getJSONArray(key);
                    List<String> items = new ArrayList<>();
                    for (int i = 0; i < array.length(); i++) {
                        JSONObject item = array.getJSONObject(i);
                        items.add(item.keys().next() + "");  // 提取詞/句子
                    }
                    dataMap.put(key, items);
                }
                runOnUiThread(() -> Toast.makeText(this, "數據加載成功", Toast.LENGTH_SHORT).show());
            }
        } catch (IOException | org.json.JSONException e) {
            runOnUiThread(() -> Toast.makeText(this, "數據加載失敗: " + e.getMessage(), Toast.LENGTH_SHORT).show());
        }
    }

    private void updateLessonSpinner(String type) {
        List<String> lessons = new ArrayList<>();
        for (String key : dataMap.keySet()) {
            if (key.startsWith(type)) {
                lessons.add(key.replace(type, "").trim());
            }
        }
        ArrayAdapter<String> lessonAdapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, lessons);
        lessonSpinner.setAdapter(lessonAdapter);
    }

    private void startDictation() {
        String selectedType = (String) typeSpinner.getSelectedItem();
        String selectedLesson = (String) lessonSpinner.getSelectedItem();
        String fullKey = selectedType + selectedLesson;
        currentItems = dataMap.get(fullKey);
        if (currentItems == null || currentItems.isEmpty()) {
            Toast.makeText(this, "無數據", Toast.LENGTH_SHORT).show();
            return;
        }
        currentIndex = 0;
        readCurrentItem();
        repeatButton.setVisibility(View.VISIBLE);
        nextButton.setVisibility(View.VISIBLE);
    }

    private void readCurrentItem() {
        if (currentIndex < currentItems.size()) {
            String item = currentItems.get(currentIndex);
            currentTextView.setText(item);
            tts.setLanguage(new Locale(currentLang));
            // API 24+ 簡化：TTS 語言檢查更可靠
            if (currentLang.equals("zh-HK") && tts.isLanguageAvailable(new Locale("zh", "HK")) < TextToSpeech.LANG_AVAILABLE) {
                Toast.makeText(this, "廣東話 TTS 未安裝，使用普通話", Toast.LENGTH_SHORT).show();
                tts.setLanguage(Locale.CHINESE);
            }
            tts.speak(item, TextToSpeech.QUEUE_FLUSH, null, null);
        } else {
            Toast.makeText(this, "完成！", Toast.LENGTH_SHORT).show();
            resetUI();
        }
    }

    public void onRepeatClick(View v) {
        readCurrentItem();
    }

    public void onNextClick(View v) {
        currentIndex++;
        readCurrentItem();
    }

    private void resetUI() {
        repeatButton.setVisibility(View.GONE);
        nextButton.setVisibility(View.GONE);
        currentTextView.setText("");
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            tts.setLanguage(Locale.CHINESE);
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }
}
