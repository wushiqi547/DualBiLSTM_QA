import os
import pickle
import tensorflow as tf
from read_utils import TextConverter, get_excel_libs
from model import Model,Config
from read_utils import get_excel_QAs

def main(_):
    model_path = os.path.join('models', Config.file_name)

    input_file = 'data/去除2和null.xlsx'
    vocab_file = os.path.join(model_path, 'vocab_label.pkl')

    # 数据处理
    converter = TextConverter(None, vocab_file, max_vocab=Config.vocab_max_size, seq_length=Config.seq_length)
    print('vocab size:',converter.vocab_size)

    # 加载上一次保存的模型
    model = Model(Config, converter.vocab_size)
    checkpoint_path = tf.train.latest_checkpoint(model_path)
    if checkpoint_path:
        model.load(checkpoint_path)


    # 获取测试库数据
    # test_libs = get_excel_libs('data/tianlong_libs.xlsx')  # 用整个库3w+
    QAs = get_excel_QAs(input_file)
    thres = int(0.8 * len(QAs))
    test_QAs = QAs[thres:]
    test_libs = [r for q,r,y in test_QAs]  # 用QAs

    test_libs_arrs = converter.libs_to_arrs(test_libs)


    # 产生匹配库向量
    save_file = checkpoint_path+'_matul_state_QAs.pkl'
    if os.path.exists(save_file) is False:
        response_matul_state = model.test_to_matul(test_libs_arrs)
        with open(save_file, 'wb') as f:
            pickle.dump(response_matul_state, f)
    else:
        with open(save_file, 'rb') as f:
            response_matul_state = pickle.load(f)

    # 测试
    print('start to testing...')
    QAY = []
    k,n = 0,0
    for query,y_response,label in test_QAs:
        input_arr,input_len = converter.text_to_arr(query)
        indexs = model.test(input_arr,input_len, response_matul_state)
        responses = converter.index_to_response(indexs, test_libs)

        QAY.append((query, y_response, responses))
        if responses[0]==y_response:
            k += 1
            print(k,'/',n)
        n += 1
    print('accuracy:',k/float(n))
    result_xls = checkpoint_path+ '_Q_for_QAs.xls'
    converter.save_to_excel(QAY, result_xls)



if __name__ == '__main__':
    tf.app.run()
