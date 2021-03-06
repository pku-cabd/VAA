import torch.nn as nn
import torch.optim as optim
import torch.backends.cudnn as cudnn
from torch.optim import lr_scheduler
import torchvision
import torchvision.transforms as transforms
import os
import torch
from a3v.droped.resnet import PreActResNet18

# Training
def train(epoch):
    print('\nEpoch: %d' % epoch)
    scheduler.step()
    net.train()
    train_loss = 0
    correct = 0
    total = 0
    for batch_idx, (inputs, targets) in enumerate(trainloader):
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs, logits = net(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
    acc = 100. * correct / total
    print('train acc: %.2f' % acc)

def test(epoch):
    global best_acc
    net.eval()
    test_loss = 0
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(testloader):
            inputs, targets = inputs.to(device), targets.to(device)
            outputs, logits = net(inputs)
            loss = criterion(outputs, targets)

            test_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

    # Save checkpoint.
    acc = 100.*correct/total
    print('valid acc: %.2f' % acc)
    if acc > best_acc:
        print('update resnet ckpt!')
        state = {
            'net': net.state_dict(),
            'acc': acc,
            'epoch': epoch,
        }
        if not os.path.isdir('checkpoint'):
            os.mkdir('checkpoint')
        torch.save(state, CLASSIFY_CKPT)
        best_acc = acc


if __name__ == '__main__':
    LOAD_CKPT = True
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    BATCH_SIZE = 128
    CLASSIFY_CKPT = './data/checkpoints/cifar/resnet.pth'

    best_acc = 0  # best test accuracy
    start_epoch = 0  # start from epoch 0 or last checkpoint epoch

    # Data
    print('==> Preparing data..')
    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
    ])

    trainset = torchvision.datasets.CIFAR10(root='./data/dataset/cifar10', train=True, download=True, transform=transform_train)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)

    testset = torchvision.datasets.CIFAR10(root='./data/dataset/cifar10', train=False, download=True, transform=transform_test)
    testloader = torch.utils.data.DataLoader(testset, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

    # Model
    print('==> Building model..')
    net = PreActResNet18()
    net = net.to(device)

    if device == 'cuda':
        net = torch.nn.DataParallel(net)
        cudnn.benchmark = True

    if LOAD_CKPT:
        # Load checkpoint.
        print('==> Resuming from checkpoint..')
        checkpoint = torch.load(CLASSIFY_CKPT)
        net.load_state_dict(checkpoint['net'])
        best_acc = checkpoint['acc']
        start_epoch = checkpoint['epoch']

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9, weight_decay=5e-4)
    scheduler = lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.1)


    for epoch in range(start_epoch, start_epoch+450):
        # train(epoch)
        test(epoch)

