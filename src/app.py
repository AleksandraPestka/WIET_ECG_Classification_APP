import numpy as np
import pandas as pd
import streamlit as st
import plotly_express as px

from sklearn.metrics import ConfusionMatrixDisplay
from datasets.mitbih import MitBih
from datasets.ptbdb import PtbDb
from datasets.ptbxl import PtbXl
from config import Config
from classification import run, run_testing
from utils import get_sample_signals


def plot_class_percentage(data, class_labels):
    data_class = data.iloc[:, -1].astype(int)
    counts = data_class.value_counts().rename('counts').sort_index()
    fig = px.pie(counts, values=counts, names=class_labels, title='Class imbalance')
    st.plotly_chart(fig)


def plot_example_ecg(data, class_labels):
    sample_signals = get_sample_signals(data)
    x = np.arange(0, data.shape[1]-1) * 8/1000

    df = pd.DataFrame()
    df['x'] = x
    for label, signal in zip(class_labels, sample_signals):
        df[label] = signal

    selected_class = st.multiselect('Select signal class', class_labels,
                                     default='N: Normal beat')
    fig = px.line(data_frame=df, x='x', y=selected_class)

    fig.update_layout(
        title='1-beat ECG for every category',
        xaxis_title='Time (ms)',
        yaxis_title='Amplitude',
        legend_title_text='Classes')
    st.plotly_chart(fig)

def plot_confusion_matrix(cm, labels):
    df = pd.DataFrame(data=cm, columns=labels, index=labels)
    fig = px.imshow(df, color_continuous_scale='Reds')
    fig.update_layout(
        title='Confusion matrix',
        xaxis_title='Predicted labels',
        yaxis_title='True labels',
        legend_title_text='percentage')
    st.plotly_chart(fig)

def upload_new_data():
    uploaded_file = st.file_uploader("Upload CSV file with ECG signals", type=['.csv'])
    if uploaded_file is not None:
        new_data = pd.read_csv(uploaded_file, header=None)
        new_data.name = uploaded_file.name
        return new_data


def get_dataset_class(option):
    if option == "MITBIH":
        return MitBih()
    else:
        return PtbDb()

def testing_mode():
    new_data = upload_new_data()

    if new_data is not None:
        try:
            if new_data.name.startswith('mitbih'):
                option = 'MITBIH' 
            elif new_data.name.startswith('ptbdb'):
                option = 'PTBDB'
            else:
                raise ValueError

            dataset = get_dataset_class(option)
            st.spinner()
            with st.spinner(text='Testing in progress...'):
                conf_matrix, loss, acc_score = run_testing(new_data, 
                                                        Config.model_dir, 
                                                        dataset.NAME)
                st.success('Done')
                st.write(f'Accuracy score: {acc_score:.2f}')
                st.write(f'Loss: {loss:.2f}')
                plot_confusion_matrix(conf_matrix, dataset.CLASS_LABELS)
        except:
            st.error('Provide valid test file!')

if __name__ == '__main__':
    st.title('ECG Classification App')
    st.header('Dataset visualization')

    option = st.selectbox("Select available dataset for visualization", ("MITBIH", "PTBDB"))
    dataset = get_dataset_class(option)

    train, test = dataset.load_data(Config.data_dir)
    plot_class_percentage(train, dataset.CLASS_LABELS)
    plot_example_ecg(train, dataset.CLASS_LABELS)

    st.header('Training')
    form = st.form(key='training')
    option = form.selectbox("Select dataset to train model", ("MITBIH", "PTBDB"))
    submit = form.form_submit_button('Train')
    if submit:
        dataset = get_dataset_class(option)
        st.spinner()
        with st.spinner(text='Training in progress...'):
            run(dataset)
            st.success('Done')

    st.header('Testing')
    testing_mode()

    st.header("Heart rate")
    option = st.selectbox("Select patient",
                          ("Patient 1", "Patient 2", "Patient 3", "Patient 4",
                           "Patient 5", "Patient 6", "Patient 7"))

    patient = PtbXl()
    ecg = patient.load_data(Config.data_dir, option)

    patient.show_metadata(Config.data_dir, option)
    patient.line_plot(ecg)

    bpm = patient.calculate_heart_rate(ecg)
    st.write(bpm, " BPM")
